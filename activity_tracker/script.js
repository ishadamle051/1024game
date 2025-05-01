let activities = JSON.parse(localStorage.getItem("activities")) || [];

function displayActivities() {
    const activityList = document.getElementById("activity-list");
    activityList.innerHTML = "";
    activities.forEach((activity, index) => {
        const li = document.createElement("li");
        li.innerHTML = `
            <div>
                ${activity.name} - ${activity.category} 
                <small>Added: ${new Date().toLocaleString()}</small>
            </div>
            <div>
                <button class="delete-btn" onclick="deleteActivity(${index})">❌</button>
            </div>
        `;
        activityList.appendChild(li);
    });
}

function addActivity() {
    const activityName = document.getElementById("activity-name").value;
    const category = document.getElementById("category").value;

    if (activityName && category) {
        const newActivity = { name: activityName, category: category };
        activities.push(newActivity);
        localStorage.setItem("activities", JSON.stringify(activities));
        displayActivities();
        document.getElementById("activity-name").value = "";  // Reset input field
    } else {
        alert("Please fill in both fields.");
    }
}

function deleteActivity(index) {
    activities.splice(index, 1);
    localStorage.setItem("activities", JSON.stringify(activities));
    displayActivities();
}

// Initial load of saved activities
displayActivities();
