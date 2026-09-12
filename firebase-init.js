// firebase-init.js
// Punto único de inicialización de Firebase para todo el sitio.
// Impórtalo desde cualquier página con:
//   import { auth, db } from './firebase-init.js';   (o '../firebase-init.js' si está en subcarpeta)
//
// IMPORTANTE: esta apiKey está pensada para ser pública (identifica el proyecto,
// no autoriza nada por sí sola). La seguridad real vive en firestore.rules.

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import {
    getAuth,
    onAuthStateChanged,
    signOut,
    updateProfile
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import {
    getFirestore,
    serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

const firebaseConfig = {
    apiKey: "AIzaSyCvGL-OS6zimRbZerqBKWgJ7WYERlDUn5w",
    authDomain: "kazokugaming-758d5.firebaseapp.com",
    projectId: "kazokugaming-758d5",
    storageBucket: "kazokugaming-758d5.firebasestorage.app",
    messagingSenderId: "577769463176",
    appId: "1:577769463176:web:50753c43c302ca321aee3d"
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

export { onAuthStateChanged, signOut, updateProfile, serverTimestamp };
