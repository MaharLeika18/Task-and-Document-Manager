import { getAuth, onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, GoogleAuthProvider, signInWithPopup, FacebookAuthProvider } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-auth.js";
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-app.js";
import { getFirestore, setDoc, doc, getDoc } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-firestore.js";

const logout_btn = document.getElementById("logout_btn");

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

logout_btn.addEventListener("click", () => {
    signOut(auth).then(() => {
        console.log("// Sign-out successful.")
        window.location.href = "/logout";
    }).catch((error) => {
      // An error happened.
    });
});