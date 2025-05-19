function process_login(){
    let userPicker = document.querySelector("#usernameLog")
    let passPicker = document.querySelector("#passwordLog")
    let data = "username=" + encodeURIComponent(userPicker.value)
    data += "&password=" + encodeURIComponent(passPicker.value)
    fetch("http://localhost:8080/sessions/auth", {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": authorizationHeader()
        },
        method: "POST",
        body: data,
    })
    .then(function(response){
        //console.log("The response is ", response.text())
        //set whatever 
        if (response.status === 200){
            return response.json()
        } else{
            throw new Error("Invalid login credentials");
        }
    })
    .then(function(data) {
        console.log("Login successful:", data);
        createSessionID(); // Fetch session data after login
        let loginbtn = document.querySelector("#loginBtn")
        loginbtn.innerHTML = "Logout"
        loginbtn.onclick = process_logout
    })
    .catch(function(error) {
        console.error("Login failed:", error.message);
        alert("Login failed. Please check your username and password.");
    });
}

function process_logout(){
    fetch("http://localhost:8080/sessions", {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": authorizationHeader()
        },
        method: "DELETE",
    })
    .then(function(response){
        if (response.status == 200){
            alert("Logging out")
            document.querySelector("section").innerHTML = ""
            let loginbtn = document.querySelector("#loginBtn")
            loginbtn.innerHTML = "Login"
            loginbtn.onclick = openLoginModal
        }
        else{
            alert("Could not log out")
        }
        console.log("The response is ", response.text())
    })
}

function authorizationHeader(){
    let sessionID = localStorage.getItem("sessionID")
    if (sessionID) {
        console.log("Found a session id in the auth header:", sessionID)
        return `Bearer ${sessionID}`
    } else {
        return null
    }
}

function createSessionID(){
    fetch("http://localhost:8080/sessions", {
        headers: {
            "Authorization": authorizationHeader()
        }
    })
    .then(function(response){
        if (response.status == 200){
            return response.json();
        } else {
            throw new Error("Failed to retrieve session data. Status: " + response.status)
        }
    })
    .then(function(session) {
        localStorage.setItem('sessionID', session.id)
        console.log("Session data:", session)
        if (session.data) {
            show_artists();
        }
    })
    .catch(function(error) {
        console.error("Error creating session:", error.message);
    });
}

createSessionID()