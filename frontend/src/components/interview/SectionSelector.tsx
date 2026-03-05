"use client";

import { useInterviewStore } from "@/store/interviewStore";
import { useEffect } from "react";
import { interviewService } from "@/lib/interviewService";

export default function SectionSelector() {
    const sections = useInterviewStore(s => s.sections);
    const startSection = useInterviewStore(s => s.startSection);
    const error = useInterviewStore(s => s.error);

    // If sections wasn't fetched yet for some reason, fetch them.
    useEffect(() => {
        if (sections.length === 0) {
            interviewService.getSections().then(sect => {
                useInterviewStore.setState({ sections: sect });
            }).catch(e => console.error(e));
        }
    }, [sections.length]);

    // Format status for display
    const formatStatus = (status: string) => {
        return status.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-6">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-sm border border-gray-200 p-8">
                <div className="mb-6 text-center">
                    <h1 className="text-2xl font-bold text-gray-800">Interview Sections</h1>
                    <p className="text-gray-500 text-sm mt-1">Please complete all the sections below.</p>
                </div>

                {error && (
                    <div className="mb-6 bg-red-50 text-red-600 border border-red-200 p-3 rounded-md text-sm font-medium">
                        {error}
                    </div>
                )}

                <div className="space-y-4">
                    {sections.map(section => (
                        <div key={section.id} className="border border-gray-200 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all hover:shadow-md">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-800 capitalize">
                                    {section.section_type} Section
                                </h3>
                                <div className="text-sm text-gray-500 mt-2 flex flex-wrap gap-x-4 gap-y-1">
                                    <span className="flex items-center gap-1">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                        {section.duration_minutes}m
                                    </span>
                                    <span className="flex items-center gap-1">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                                        {section.completed_questions}/{section.total_questions} Questions
                                    </span>
                                    <span className={`font-medium ${section.status === 'completed' ? 'text-green-600' : 'text-blue-600'}`}>
                                        {formatStatus(section.status)}
                                    </span>
                                </div>
                            </div>

                            <div className="flex-shrink-0">
                                {section.status === "completed" ? (
                                    <button disabled className="w-full sm:w-auto px-6 py-2.5 bg-gray-100 text-gray-500 font-bold uppercase rounded-md text-xs cursor-not-allowed border border-gray-200">
                                        Completed
                                    </button>
                                ) : section.status === "in_progress" ? (
                                    <button
                                        onClick={() => startSection(section.section_type)}
                                        className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase rounded-md text-xs transition-colors shadow-sm"
                                    >
                                        Resume
                                    </button>
                                ) : (
                                    <button
                                        onClick={() => startSection(section.section_type)}
                                        className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold uppercase rounded-md text-xs transition-colors shadow-sm"
                                    >
                                        Start
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}

                    {sections.length === 0 && (
                        <div className="text-center py-8">
                            <p className="text-gray-500 italic">No sections available.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
