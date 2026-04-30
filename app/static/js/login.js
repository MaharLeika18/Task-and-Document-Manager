import { getAuth, signInWithEmailAndPassword, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-auth.js";
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-app.js";
import { getFirestore, doc, getDoc } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyDSakODQ8LWmOV7Q6qTVYhPwnErWBdZIDY",
    authDomain: "ccs-task-management-system.firebaseapp.com",
    projectId: "ccs-task-management-system",
    storageBucket: "ccs-task-management-system.firebasestorage.app",
    messagingSenderId: "598303458333",
    appId: "1:598303458333:web:e1e1c2f9c37416acf372f4",
    measurementId: "G-YK4Q73CLL5"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

getRedirectResult(auth)
    .then(async (result) => {
        if (result?.user) {
            const token = await result.user.getIdToken();
            const data = await sendLoginToken(token);
            if (data.success) {
                alert("Log-in successful!");
                window.location.href = "/home";
            } else {
                alert("Login failed: " + (data.error || data.message || 'Unknown error'));
            }
        }
    })
    .catch((error) => {
        console.error('Redirect login error:', error);
    });

const login_form = document.getElementById("login-form");
const google_reg = document.getElementById("google-reg");

// EMAIL LOGIN
login_form.addEventListener('submit', async (e) => {
    e.preventDefault(); 
    
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password1").value;

    if (!email || !password) {
        alert("Please fill in all the fields.");
        return;
    }

    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        const token = await user.getIdToken();

        const data = await sendLoginToken(token);
        if (data.success) {
            alert("Log-in successful!");
            window.location.href = "/home";
        } else {
            alert("Login failed: " + (data.error || data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error(error);
        alert(`${error.code}: ${error.message}`);
    }
});

// GOOGLE LOGIN
google_reg.addEventListener("click", async (e) => {
    e.preventDefault();
    
    try {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        const token = await user.getIdToken();

        const data = await sendLoginToken(token);
        if (data.success) {
            alert("Log-in successful!");
            window.location.href = "/home";
        } else {
            alert("Login failed: " + (data.error || data.message || 'Unknown error'));
        }
    } catch (error) {
        console.error(error);
        const errorMessage = String(error.message || error || '');
        if (errorMessage.includes('Cross-Origin-Opener-Policy') || errorMessage.includes('Cross-Origin-Opener-Policy policy') || error.code === 'auth/popup-blocked') {
            const provider = new GoogleAuthProvider();
            await signInWithRedirect(auth, provider);
            return;
        }
        alert(`Google sign-in failed: ${error.message}`);
    }
});

async function sendLoginToken(token) {
    const payload = { token };
    let attempt = 0;
    let lastResponse = { success: false, message: 'Login request failed' };

    while (attempt < 2) {
        if (attempt > 0) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        const res = await fetch("/login/login_user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        lastResponse = data;

        if (data.success) {
            return data;
        }

        const message = (data.error || data.message || '').toLowerCase();
        if (!message.includes('token used too early')) {
            return data;
        }

        attempt += 1;
    }

    return lastResponse;
}
