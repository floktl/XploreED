// Debug utility functions

export const triggerBackendDebug = async () => {
    try {
        const response = await fetch('/api/debug/ai-user-titles', {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to trigger backend debug');
        console.log('Triggered backend debug for ai_user_data titles.');
    } catch (err) {
        console.error('Debug fetch error:', err);
    }
};
