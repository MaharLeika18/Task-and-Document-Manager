import { getAuth, createUserWithEmailAndPassword, GoogleAuthProvider, signInWithPopup } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-auth.js";
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-app.js";
import { getFirestore, setDoc, doc, getDoc } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyDSakODQ8LWmOV7Q6qTVYhPwnErWBdZIDY",
    authDomain: "ccs-task-management-system.firebaseapp.com",
    projectId: "ccs-task-management-system",
    storageBucket: "ccs-task-management-system.firebasestorage.app",
    messagingSenderId: "598303458333",
    appId: "1:598303458333:web:e1e1c2f9c37416acf372f4",
    measurementId: "G-YK4Q73CLL5"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

const email_reg = document.getElementById('registration-form');
const google_reg = document.getElementById("google-reg");

// EMAIL REGISTRATION
email_reg.addEventListener('submit', async (e) => {
    e.preventDefault(); 
    
    const first_name = document.getElementById("first-name").value.trim();
    const last_name = document.getElementById("last-name").value.trim();
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password1").value;
    const password2 = document.getElementById("password2").value;

    if (password !== password2) {
        alert("Passwords do not match.");
        return;
    }

    if (!first_name || !last_name || !username || !email || !password) {
        alert("Please fill in all the fields.");
        return;
    }

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        const date = new Date();
        
        const register_data = {
            uid: user.uid,
            display_name: `${first_name} ${last_name}`,
            username: username,
            email: email,
            date_created: `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`
        };
        
        const token = await user.getIdToken();
        
        // Send to Flask
        const res = await fetch("/register/register_user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token })
        });
        
        const data = await res.json();
        console.log(data)
        if (data.success) {
            await addData(register_data);
            alert("Registration successful!");
            window.location.href = "/home";
        } else {
            alert("Registration failed");
        }
    } catch (error) {
        console.error(error);
        alert(`${error.code}: ${error.message}`);
    }
});

// GOOGLE REGISTRATION
google_reg.addEventListener("click", async (e) => {
    e.preventDefault(); 
    
    try {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        const idToken = await user.getIdToken();

        const res = await fetch("/register/register_user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: idToken })
        });

        const data = await res.json();
        if (!data.success) throw new Error("Backend auth failed");

        const date = new Date();
        const register_data = {
            uid: user.uid,
            display_name: user.displayName || "User",
            username: user.displayName || user.email.split('@')[0],
            email: user.email,
            date_created: `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`,
        };

        await addData(register_data);
        alert("Registration successful!");
        window.location.href = "/home";

    } catch (error) {
        console.error(error);
        alert(`Google sign-in failed: ${error.message}`);
    }
});

async function addData(data) {
    try {
        const userRef = doc(db, "users", data.uid);
        const userSnap = await getDoc(userRef);

        if (userSnap.exists()) {
            console.log("✅ User already exists");
            window.location.href = "/home";
        } else {
            await setDoc(userRef, data);
            console.log("✅ Document written with UID: ", data.uid);
        }
    } catch (e) {
        console.error("❌ Error adding document: ", e);
        alert("Something went wrong.");
    }
}