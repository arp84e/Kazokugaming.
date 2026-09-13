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
    updateProfile,
    sendEmailVerification
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

// ============================================================
// APP CHECK (protección contra abuso/spam de cuota de Firebase)
// ============================================================
// Desactivado por defecto porque requiere una clave de sitio de reCAPTCHA v3
// que solo tú puedes generar (es específica de tu dominio). Para activarlo:
//   1. Firebase Console → App Check → registra tu app web → elige reCAPTCHA v3
//      → copia el "Site key" que te entrega.
//   2. Pega ese valor en RECAPTCHA_SITE_KEY aquí abajo.
//   3. Cambia APP_CHECK_HABILITADO a true.
//   4. Sube el cambio y pruébalo A FONDO (crear escuadrón, enviar mensaje,
//      inscribirte a un torneo) ANTES de activar "Enforce" (aplicación
//      forzada) en la consola de App Check — si activas la aplicación
//      forzada sin probar antes, puedes bloquearte a ti mismo fuera de tu
//      propia app.
const APP_CHECK_HABILITADO = false;
const RECAPTCHA_SITE_KEY = 'PON_AQUI_TU_SITE_KEY';

if (APP_CHECK_HABILITADO && RECAPTCHA_SITE_KEY && RECAPTCHA_SITE_KEY !== 'PON_AQUI_TU_SITE_KEY') {
    const { initializeAppCheck, ReCaptchaV3Provider } = await import("https://www.gstatic.com/firebasejs/10.8.0/firebase-app-check.js");
    initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider(RECAPTCHA_SITE_KEY),
        isTokenAutoRefreshEnabled: true
    });
} else if (APP_CHECK_HABILITADO) {
    console.warn('App Check está habilitado pero falta poner tu RECAPTCHA_SITE_KEY real en firebase-init.js');
}

export { onAuthStateChanged, signOut, updateProfile, sendEmailVerification, serverTimestamp };

