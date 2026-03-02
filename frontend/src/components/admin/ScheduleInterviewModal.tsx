'use client';

import { useState, useEffect } from 'react';
import { InterviewTemplate } from '@/types/interview';
import { fetchInterviewTemplates, scheduleInterview, rescheduleInterview } from '@/lib/api/interviews';
import { SchedulingApiError } from '@/types/interview';

type ModalMode = 'schedule' | 'reschedule';

interface ScheduleInterviewModalProps {
    /** 'schedule' opens a blank form; 'reschedule' prefills scheduled_at */
    mode: ModalMode;
    candidateId: string;
    candidateName: string;
    /** Required when mode === 'reschedule' */
    interviewId?: string;
    /** Prefill datetime for reschedule */
    existingScheduledAt?: string;
    onClose: () => void;
    onSuccess: () => void;
    onAuthError: () => void;
}

export default function ScheduleInterviewModal({
    mode,
    candidateId,
    candidateName,
    interviewId,
    existingScheduledAt,
    onClose,
    onSuccess,
    onAuthError,
}: ScheduleInterviewModalProps) {
    const [templates, setTemplates] = useState<InterviewTemplate[]>([]);
    const [templateId, setTemplateId] = useState('');
    // Default to current local datetime in "YYYY-MM-DDTHH:mm" format
    const nowLocal = () => {
        const d = new Date();
        // Offset by timezone so the value matches the local time in the input
        d.setSeconds(0, 0);
        const offset = d.getTimezoneOffset() * 60000;
        return new Date(d.getTime() - offset).toISOString().slice(0, 16);
    };

    const [scheduledAt, setScheduledAt] = useState(nowLocal);
    const [loading, setLoading] = useState(false);
    const [templatesLoading, setTemplatesLoading] = useState(false);
    const [error, setError] = useState('');

    // ─── Prefill for reschedule ───────────────────────────────────────────────
    useEffect(() => {
        if (mode === 'reschedule' && existingScheduledAt) {
            setScheduledAt(new Date(existingScheduledAt).toISOString().slice(0, 16));
        }
    }, [mode, existingScheduledAt]);

    // ─── Load templates (schedule mode only) ─────────────────────────────────
    useEffect(() => {
        if (mode !== 'schedule') return;
        setTemplatesLoading(true);
        fetchInterviewTemplates()
            .then((data) => {
                const active = data.filter((t) => t.is_active);
                setTemplates(active);
                if (active.length > 0) setTemplateId(active[0].id);
            })
            .catch((err: SchedulingApiError) => {
                if (err.status === 401 || err.status === 403) onAuthError();
                // Fallback: use a valid 24-char hex ObjectId placeholder
                // so the backend doesn't reject it while templates are unavailable
                setTemplates([]);
                setTemplateId('');
            })
            .finally(() => setTemplatesLoading(false));
    }, [mode, onAuthError]);

    // ─── Submit ───────────────────────────────────────────────────────────────
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!scheduledAt) {
            setError('Please select a date and time.');
            return;
        }

        if (mode === 'schedule' && !templateId) {
            setError('Please select an interview template.');
            return;
        }

        setLoading(true);
        try {
            const isoAt = new Date(scheduledAt).toISOString();

            if (mode === 'schedule') {
                await scheduleInterview({ candidate_id: candidateId, template_id: templateId, scheduled_at: isoAt });
            } else {
                if (!interviewId) throw new Error('Missing interview ID for reschedule');
                await rescheduleInterview(interviewId, { scheduled_at: isoAt });
            }
            onSuccess();
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) {
                onAuthError();
                return;
            }
            if (apiErr.status === 409) {
                setError('Candidate already has an active interview (scheduled or in progress).');
            } else {
                setError(apiErr.detail || 'An unexpected error occurred.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl w-full max-w-md shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className="text-xl font-bold text-white">
                                {mode === 'schedule' ? 'Schedule Interview' : 'Reschedule Interview'}
                            </h2>
                            <p className="text-blue-100 text-sm mt-0.5">Candidate: <span className="font-semibold">{candidateName}</span></p>
                        </div>
                        <button
                            onClick={onClose}
                            disabled={loading}
                            className="text-blue-200 hover:text-white transition-colors p-1 rounded"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Error banner */}
                    {error && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            <svg className="w-4 h-4 mt-0.5 shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                            </svg>
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Template selector (schedule only) */}
                    {mode === 'schedule' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1.5">
                                Interview Template <span className="text-red-500">*</span>
                            </label>
                            {templatesLoading ? (
                                <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
                                    <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Loading templates…
                                </div>
                            ) : (
                                <select
                                    value={templateId}
                                    onChange={(e) => setTemplateId(e.target.value)}
                                    required
                                    disabled={loading}
                                    className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white disabled:bg-gray-50"
                                >
                                    {templates.length === 0 && (
                                        <option value="">No active templates available</option>
                                    )}
                                    {templates.map((t) => (
                                        <option key={t.id} value={t.id}>
                                            {t.name}
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>
                    )}

                    {/* Date & Time picker */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1.5">
                            {mode === 'reschedule' ? 'New ' : ''}Date & Time (IST / Local) <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="datetime-local"
                            value={scheduledAt}
                            onChange={(e) => setScheduledAt(e.target.value)}
                            required
                            disabled={loading}
                            className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
                        />
                        <p className="mt-1 text-xs text-gray-600">Defaults to now — adjust as needed.</p>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={loading}
                            className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading || (mode === 'schedule' && !templateId)}
                            className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    {mode === 'schedule' ? 'Scheduling…' : 'Rescheduling…'}
                                </>
                            ) : mode === 'schedule' ? (
                                'Schedule Interview'
                            ) : (
                                'Confirm Reschedule'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
