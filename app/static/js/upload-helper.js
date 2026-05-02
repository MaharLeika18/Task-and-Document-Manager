window.uploadDriveFiles = async function uploadDriveFiles(options) {
    const {
        files = [],
        projectUid = null,
        taskName = null,
        folderId = null,
        endpoint = '/files/api/upload',
        onStatus = null,
        onFileStart = null,
        onFileSuccess = null,
        onFileError = null,
        onComplete = null,
    } = options || {};

    const fileList = Array.from(files || []);
    if (!fileList.length) {
        if (typeof onStatus === 'function') {
            onStatus('Select at least one file to upload.', 'error');
        }
        return { success: false, message: 'No files selected' };
    }

    const results = [];

    for (let index = 0; index < fileList.length; index += 1) {
        const file = fileList[index];
        if (typeof onFileStart === 'function') {
            onFileStart({ file, index, total: fileList.length });
        }

        const formData = new FormData();
        formData.append('file', file);
        if (folderId) {
            formData.append('folder_id', folderId);
        }
        if (projectUid) {
            formData.append('project_uid', projectUid);
        }
        if (taskName) {
            formData.append('task_name', taskName);
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                if (typeof onFileError === 'function') {
                    onFileError({ file, index, total: fileList.length, data });
                }
                results.push({ success: false, file, data });
                continue;
            }

            if (typeof onFileSuccess === 'function') {
                onFileSuccess({ file, index, total: fileList.length, data });
            }
            results.push({ success: true, file, data });
        } catch (error) {
            if (typeof onFileError === 'function') {
                onFileError({ file, index, total: fileList.length, error });
            }
            results.push({ success: false, file, error });
        }
    }

    const success = results.some(result => result.success);
    const allSucceeded = results.length > 0 && results.every(result => result.success);

    if (typeof onComplete === 'function') {
        onComplete({ results, success, allSucceeded });
    }

    return {
        success,
        allSucceeded,
        results,
    };
};
