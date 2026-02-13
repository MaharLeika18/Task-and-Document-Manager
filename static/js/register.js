import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.9.0/firebase-analytics.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, GoogleAuthProvider, signInWithPopup, FacebookAuthProvider } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-auth.js";
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-app.js";
import { getFirestore, collection, addDoc } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-firestore.js";
import { setDoc, doc, getDoc } from "https://www.gstatic.com/firebasejs/11.7.1/firebase-firestore.js";

// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries
require('dotenv').config();

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: "ccs-task-management-system.firebaseapp.com",
    projectId: "ccs-task-management-system",
    storageBucket: "ccs-task-management-system.firebasestorage.app",
    messagingSenderId: "598303458333",
    appId: "1:598303458333:web:ca02e75c4f9c5a7ef372f4",
    measurementId: "G-RE3ZBEV7VM"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

email_reg = document.getElementById('registration-form');

email_reg.addEventListener('submit', (e) => {
    const first_name = document.getElementById("first-name").value.trim();
    const last_name = document.getElementById("last-name").value.trim();
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password1").value;
    const password2 = document.getElementById("password2").value;

    if (password !== password2) {
        alert("Passwords do not match.");
        return;
    }

    if (!first_name || !last_name || !username || !email || !password || !password2) {
        alert("Please fill in all the fields.");
        return;
    }
    
    //will fix the logic for it to send the token ID to flask and then it'll verify the token then it'll coook the login na
    createUserWithEmailAndPassword(auth, email, password).then((userCredential) => {
        const user = userCredential.user;
        const date = new Date();
        const register_data = {
            uid: user.uid,
            display_name: `${first_name} ${last_name}`,
            username: username,
            email: email,
            date_created: `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`
        };
        return addData(register_data);
    })
    .then(() => {
        alert("Registration successful!");
    })
    .catch((error) => {
        alert(`${error.code}: ${error.message}`);
    });

    forms.reset();
})

const provider = new GoogleAuthProvider();
    signInWithPopup(auth, provider)
    .then((result) => {
        // This gives you a Google Access Token. You can use it to access the Google API.
        const credential = GoogleAuthProvider.credentialFromResult(result);
        const token = credential.accessToken;
        console.log(token);
        // The signed-in user info.
        const user = result.user;
        console.log(user);
        const date = new Date();
        const register_data = {
            uid: user.uid,
            display_name: user.displayName,
            username: user.displayName,
            email: user.email,
            date_created: `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`
        };
        return addData(register_data);
        // IdP data available using getAdditionalUserInfo(result)
        // ...
    }).catch((error) => {
      // Handle Errors here.
        const errorCode = error.code;
        const errorMessage = error.message;
        // The email of the user's account used.
        const email = error.customData.email;
        // The AuthCredential type that was used.
        const credential = GoogleAuthProvider.credentialFromError(error);
        alert(`${error.code}: ${error.message}`);
        // ...
    });


async function addData(data) {
    try {
        const userRef = doc(db, "users", data.uid);
        const userSnap = await getDoc(userRef);

        if (userSnap.exists()) {
            console.log("✅ User already exists");
            alert("User already exists");
            window.location.href = "/home.html";
        } else {
            await setDoc(userRef, data); // this is enough
            console.log("✅ Document written with UID: ", data.uid);
            window.location.href="/home.html";
        }
    } catch (e) {
        console.error("❌ Error adding document: ", e);
        alert("Something went wrong.");
    }
}



const user = auth.currentUser;
console.log(user)