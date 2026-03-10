'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useInterviewStore } from '@/store/interviewStore';

export default function ThankYouPage() {
    const router = useRouter();
    const { user, isAuthenticated, _hasHydrated } = useAuthStore();
    const terminate = useInterviewStore((s) => s.terminate);

    useEffect(() => {
        if (!_hasHydrated) return;
        if (!isAuthenticated || !user) {
            router.push('/login/candidate');
            return;
        }
        if (user.role !== 'candidate') {
            router.push('/candidate');
            return;
        }
    }, [_hasHydrated, isAuthenticated, user, router]);

    const handleReturnToDashboard = () => {
        terminate();
        router.push('/candidate');
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 md:p-12 text-center">
                {/* Success Icon */}
                <div className="flex justify-center mb-6">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                </div>

                {/* Thank You Message */}
                <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                    Thank You!
                </h1>
                <p className="text-lg text-gray-600 mb-2">
                    Your interview has been successfully submitted.
                </p>
                <p className="text-base text-gray-500 mb-8">
                    Our team will review your responses and get back to you soon.
                </p>

                {/* Information Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8 text-left">
                    <div className="flex items-start gap-3">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                            <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
                            <ul className="text-sm text-blue-800 space-y-1">
                                <li>• Your interview responses are being reviewed</li>
                                <li>• You will receive an email with next steps</li>
                                <li>• Check your dashboard for updates</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Return Button */}
                <button
                    onClick={handleReturnToDashboard}
                    className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm"
                >
                    Return to Dashboard
                </button>
            </div>
        </div>
    );
}
