let taskCount = 0;

function addTask() {
    taskCount++;
    const container = document.getElementById('tasks-container');

    const taskRow = document.createElement('div');
    taskRow.classList.add('task-row');
    taskRow.id = `task-${taskCount}`;

    let taskCount = 0;

    function addTask() {
        taskCount++;
        const container = document.getElementById('tasks-container');

        // Build current user checkbox
        let membersHTML = `
            <div>
                <label>
                    <input type="checkbox" name="tasks[${taskCount}][members]" value="${CURRENT_USER.uid}" checked>
                    ${CURRENT_USER.name} (You)
                </label>
            </div>
        `;

        // Build checkboxes for all other members
        ALL_MEMBERS.forEach(member => {
            membersHTML += `
                <div>
                    <label>
                        <input type="checkbox" name="tasks[${taskCount}][members]" value="${member.uid}">
                        ${member.name}
                    </label>
                </div>
            `;
        });

        const taskRow = document.createElement('div');
        taskRow.classList.add('task-row');
        taskRow.id = `task-${taskCount}`;

        taskRow.innerHTML = `
            <span class="task-number">#${taskCount}</span>

            <input
                type="text"
                name="tasks[${taskCount}][name]"
                placeholder="Task name"
                required
            >

            <select name="tasks[${taskCount}][priority]">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
            </select>

            <select name="tasks[${taskCount}][status]">
                <option value="todo">To Do</option>
                <option value="in-progress">In Progress</option>
                <option value="done">Done</option>
            </select>

            <label>Assign member/s:</label>
            ${membersHTML}

            <button type="button" class="remove-task-btn" onclick="removeTask(${taskCount})">✕</button>
        `;

        container.appendChild(taskRow);
    }

    function removeTask(id) {
        const task = document.getElementById(`task-${id}`);
        if (task) task.remove();
    }

    container.appendChild(taskRow);
}

function removeTask(id) {
    const task = document.getElementById(`task-${id}`);
    if (task) task.remove();
}