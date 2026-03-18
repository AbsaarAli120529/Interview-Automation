"""
session_router.py (Refactored for SQLAlchemy with SocketIO)
=================
Endpoints used by the interview shell (InterviewShell, InterviewService, ControlWebSocket).

Routes (all under /api/v1 prefix added in main.py):
  SocketIO /proctoring/ws                – SocketIO proctoring / control channel
  SocketIO /answer/ws                    – SocketIO answer transcription channel
  SocketIO /proctoring/media/ws          – SocketIO media streaming channel
  POST /session/start               – Start a session, returns {state}
  GET  /question/next               – Return next unanswered question
  POST /submit/submit               – Record answer, return next state
  POST /proctoring/event            – Acknowledge a proctoring event

Auth:
  REST  → Authorization: Bearer <jwt>  +  X-Interview-Id: <session_id>
  SocketIO → HANDSHAKE event {type, interview_id, candidate_token}
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_router import get_current_active_user
from app.db.sql.session import get_db_session, AsyncSessionLocal
from app.db.sql.models.user import User
from app.db.sql.enums import UserRole
from app.services.interview_session_sql_service import InterviewSessionSQLService

logger = logging.getLogger(__name__)

router = APIRouter()

# SocketIO instance will be set from main.py
_sio = None
# Store session data per sid
_session_data = {}

def set_sio(sio_instance):
    """Set the SocketIO instance from main.py"""
    global _sio
    _sio = sio_instance
    _register_socketio_handlers()

def _register_socketio_handlers():
    """Register SocketIO event handlers"""
    if not _sio:
        return
    
    @_sio.on('connect', namespace='/proctoring/ws')
    async def proctoring_connect(sid, environ):
        logger.info(f"[proctoring_ws] SocketIO connection accepted: {sid}")
        return True
    
    @_sio.on('disconnect', namespace='/proctoring/ws')
    async def proctoring_disconnect(sid):
        logger.info(f"[proctoring_ws] SocketIO disconnected: {sid}")
    
    @_sio.on('HANDSHAKE', namespace='/proctoring/ws')
    async def proctoring_handshake(sid, data):
        """Handle HANDSHAKE event for proctoring channel"""
        try:
            session_id_str = data.get("interview_id", "")
            candidate_token = data.get("candidate_token", "")
            
            try:
                session_id = uuid.UUID(session_id_str)
                
                async with AsyncSessionLocal() as session:
                    try:
                        validation_result = await InterviewSessionSQLService.validate_session(session, session_id)
                        candidate_id = uuid.UUID(validation_result.get("candidate_id", ""))
                        logger.info(f"[proctoring_ws] Session validated: {session_id}")
                        
                        await _sio.emit('HANDSHAKE_ACK', {
                            "heartbeat_interval_sec": 30,
                        }, room=sid, namespace='/proctoring/ws')
                        logger.info("[proctoring_ws] HANDSHAKE_ACK sent")
                        return
                    except HTTPException as e:
                        logger.warning(f"[proctoring_ws] Session validation failed: {e.detail}")
                    except Exception as e:
                        logger.error(f"[proctoring_ws] Error validating session: {e}")
            except (ValueError, TypeError) as e:
                logger.warning(f"[proctoring_ws] Invalid session_id format: {session_id_str}, error: {e}")
            
            await _sio.emit('ERROR', {
                "detail": "Invalid session or session not found",
            }, room=sid, namespace='/proctoring/ws')
            await _sio.disconnect(sid, namespace='/proctoring/ws')
            
        except Exception as e:
            logger.error(f"[proctoring_ws] Error in handshake: {e}", exc_info=True)
            await _sio.emit('ERROR', {
                "detail": "Internal server error",
            }, room=sid, namespace='/proctoring/ws')
    
    @_sio.on('HEARTBEAT', namespace='/proctoring/ws')
    async def proctoring_heartbeat(sid, data):
        """Handle HEARTBEAT event"""
        await _sio.emit('HEARTBEAT_ACK', {}, room=sid, namespace='/proctoring/ws')
    
    @_sio.on('TERMINATE', namespace='/proctoring/ws')
    async def proctoring_terminate(sid, data):
        """Handle TERMINATE event"""
        reason = data.get("reason", "Unknown reason")
        await _sio.emit('TERMINATE', {
            "payload": {"reason": reason}
        }, room=sid, namespace='/proctoring/ws')
        await _sio.disconnect(sid, namespace='/proctoring/ws')
    
    # Answer WebSocket handlers
    @_sio.on('connect', namespace='/answer/ws')
    async def answer_connect(sid, environ):
        logger.info(f"[answer_ws] SocketIO connection accepted: {sid}")
        return True
    
    @_sio.on('disconnect', namespace='/answer/ws')
    async def answer_disconnect(sid):
        logger.info(f"[answer_ws] SocketIO disconnected: {sid}")
        # Cleanup session data on disconnect
        if sid in _session_data:
            session_data = _session_data[sid]
            recognition_session = session_data.get('recognition_session')
            if recognition_session:
                try:
                    await recognition_session.stop()
                except:
                    pass
                transcript_id = session_data.get('transcript_id')
                if transcript_id:
                    try:
                        from app.services.azure_speech_service import azure_speech_service
                        azure_speech_service.remove_recognition_session(transcript_id)
                    except:
                        pass
            del _session_data[sid]
    
    @_sio.on('START_ANSWER', namespace='/answer/ws')
    async def answer_start(sid, data):
        """Handle START_ANSWER event"""
        try:
            question_id = data.get("question_id")
            logger.info(f"[answer_ws] Starting transcription for question {question_id}")
            
            from app.services.azure_speech_service import azure_speech_service
            
            transcript_id = str(uuid.uuid4())
            partial_text = ""
            
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            
            def send_partial(text: str):
                nonlocal partial_text
                partial_text = text
                logger.info(f"\n[STT PARTIAL] {text}")
                try:
                    asyncio.run_coroutine_threadsafe(
                        _sio.emit('TRANSCRIPT_PARTIAL', {
                            "text": text
                        }, room=sid, namespace='/answer/ws'),
                        loop
                    )
                except Exception as e:
                    logger.error(f"[answer_ws] Error sending partial transcript: {e}")
            
            def send_final(text: str):
                nonlocal partial_text
                partial_text = text
                logger.info(f"\n[STT FINAL] {text}")
                try:
                    asyncio.run_coroutine_threadsafe(
                        _sio.emit('TRANSCRIPT_FINAL', {
                            "text": text
                        }, room=sid, namespace='/answer/ws'),
                        loop
                    )
                except Exception as e:
                    logger.error(f"[answer_ws] Error sending final transcript: {e}")
            
            is_azure_mode = azure_speech_service._initialized
            logger.info(f"\n[STT STATUS] Azure Speech Service: {'INITIALIZED' if is_azure_mode else 'MOCK MODE'}")
            
            recognition_session = azure_speech_service.create_recognition_session(
                session_id=transcript_id,
                on_partial_result=send_partial,
                on_final_result=send_final,
            )
            
            # Store session data
            _session_data[sid] = {
                'recognition_session': recognition_session,
                'transcript_id': transcript_id,
                'partial_text': partial_text
            }
            
            await _sio.emit('STARTED', {
                "message": "Ready to receive audio"
            }, room=sid, namespace='/answer/ws')
            
        except Exception as e:
            logger.error(f"[answer_ws] Error in START_ANSWER: {e}", exc_info=True)
            await _sio.emit('ERROR', {
                "detail": "Failed to start transcription"
            }, room=sid, namespace='/answer/ws')
    
    @_sio.on('audio_data', namespace='/answer/ws')
    async def answer_audio_data(sid, data):
        """Handle audio data chunks"""
        try:
            session_data = _session_data.get(sid, {})
            recognition_session = session_data.get('recognition_session')
            
            if recognition_session:
                # data should be base64 encoded string
                import base64
                if isinstance(data, dict) and 'data' in data:
                    audio_chunk = base64.b64decode(data['data'])
                elif isinstance(data, str):
                    audio_chunk = base64.b64decode(data)
                else:
                    logger.warning(f"[answer_ws] Unexpected audio data format: {type(data)}")
                    return
                
                recognition_session.push_audio(audio_chunk)
            else:
                logger.warning("[answer_ws] No recognition session available")
        except Exception as e:
            logger.error(f"[answer_ws] Error processing audio data: {e}", exc_info=True)
    
    @_sio.on('END_ANSWER', namespace='/answer/ws')
    async def answer_end(sid, data):
        """Handle END_ANSWER event"""
        try:
            session_data = _session_data.get(sid, {})
            recognition_session = session_data.get('recognition_session')
            partial_text = session_data.get('partial_text', '')
            
            final_text = partial_text.strip() if partial_text else ""
            
            if recognition_session:
                try:
                    await recognition_session.stop()
                    session_final = recognition_session.get_final_transcript()
                    if session_final and session_final.strip():
                        final_text = session_final
                except Exception as e:
                    logger.error(f"[answer_ws] Error stopping recognition session: {e}")
            
            if not final_text or not final_text.strip():
                final_text = partial_text.strip() if partial_text else "No speech detected."
            
            await _sio.emit('TRANSCRIPT_FINAL', {
                "text": final_text
            }, room=sid, namespace='/answer/ws')
            
            await _sio.emit('ANSWER_READY', {
                "transcript_id": final_text
            }, room=sid, namespace='/answer/ws')
            
            # Cleanup
            if recognition_session:
                transcript_id = session_data.get('transcript_id')
                if transcript_id:
                    from app.services.azure_speech_service import azure_speech_service
                    azure_speech_service.remove_recognition_session(transcript_id)
            
            # Remove session data
            if sid in _session_data:
                del _session_data[sid]
            
            await _sio.disconnect(sid, namespace='/answer/ws')
            
        except Exception as e:
            logger.error(f"[answer_ws] Error in END_ANSWER: {e}", exc_info=True)
    
    # Media WebSocket handlers (simplified - just accepts data)
    @_sio.on('connect', namespace='/proctoring/media/ws')
    async def media_connect(sid, environ):
        logger.info(f"[media_ws] SocketIO connection accepted: {sid}")
        return True
    
    @_sio.on('disconnect', namespace='/proctoring/media/ws')
    async def media_disconnect(sid):
        logger.info(f"[media_ws] SocketIO disconnected: {sid}")
    
    @_sio.on('media_data', namespace='/proctoring/media/ws')
    async def media_data(sid, data):
        """Handle media data (video/audio frames) - just acknowledge"""
        # Media data is received but not processed in this mock version
        pass


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_current_candidate(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only candidates can access this endpoint")
    return current_user

def validate_uuid(id_str: str) -> uuid.UUID:
    try:
        return uuid.UUID(id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID: {id_str}",
        )


# ─── REST endpoints ────────────────────────────────────────────────────────────

@router.post("/session/start")
async def session_start(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id
    
    # Ensures the session exists and belongs to the candidate
    await InterviewSessionSQLService.validate_session(session, session_id, candidate_id)

    return {"state": "IN_PROGRESS"}


@router.get("/question/next")
async def question_next(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id

    return await InterviewSessionSQLService.get_session_state(session, session_id, candidate_id)


@router.get("/candidate/interview/sections")
async def list_sections(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all sections for the current interview session."""
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    return await InterviewSessionSQLService.get_sections(session, session_id, current_user.id)


from pydantic import BaseModel
from typing import Optional

class StartSectionRequest(BaseModel):
    section_id: Optional[str] = None
    section_type: Optional[str] = None

@router.post("/candidate/interview/start-section")
async def start_section(
    payload: StartSectionRequest,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    """Start a specific section, making it the active section."""
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)

    if payload.section_id:
        section_id_uuid = validate_uuid(payload.section_id)
    elif payload.section_type:
        sections = await InterviewSessionSQLService.get_sections(session, session_id, current_user.id)
        section = next((s for s in sections if s["section_type"] == payload.section_type), None)
        if not section:
            raise HTTPException(status_code=404, detail="Section type not found")
        section_id_uuid = validate_uuid(section["id"])
    else:
        raise HTTPException(status_code=400, detail="Must provide section_id or section_type")
    
    return await InterviewSessionSQLService.start_section(session, session_id, section_id_uuid, current_user.id)


@router.post("/submit/submit")
async def submit_answer(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    candidate_id = current_user.id

    return await InterviewSessionSQLService.submit_answer(session, session_id, candidate_id, payload)


@router.get("/session/summary")
async def get_session_summary(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Returns mock evaluation summary for the completed interview session.
    Requires X-Interview-Id: <session_id> header.
    """
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")

    session_id = validate_uuid(x_interview_id)
    return await InterviewSessionSQLService.get_summary(session, session_id, current_user.id)


@router.post("/proctoring/event")
async def proctoring_event(
    payload: dict,
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")
        
    session_id = validate_uuid(x_interview_id)
    await InterviewSessionSQLService.validate_session(session, session_id, current_user.id)
    
    logger.info(
        "[proctoring_event] session=%s user=%s event=%s",
        session_id,
        str(current_user.id),
        payload.get("event_type"),
    )
    return {"acknowledged": True}


@router.post("/candidate/interview/complete-section")
async def complete_section(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark the current section as completed and return to section selector."""
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")
    
    session_id = validate_uuid(x_interview_id)
    return await InterviewSessionSQLService.complete_current_section(session, session_id, current_user.id)


@router.post("/session/complete")
async def complete_interview(
    x_interview_id: Optional[str] = Header(None, alias="X-Interview-Id"),
    current_user: User = Depends(_get_current_candidate),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Allow candidate to submit/complete the interview at any time.
    Marks the interview session as completed and redirects to thank you page.
    """
    if not x_interview_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Interview-Id header is required")
    
    session_id = validate_uuid(x_interview_id)
    result = await InterviewSessionSQLService.complete_session(session, session_id, current_user.id)
    
    logger.info(f"[complete_interview] Session {session_id} completed by candidate {current_user.id}")
    return result
