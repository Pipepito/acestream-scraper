import i18next from 'i18next';
import { initReactI18next } from 'react-i18next';
import { en, es } from './resources';

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: typeof en;
    returnNull: false;
    keySeparator: false;
    nsSeparator: false;
  }
}

// Core messages are bundled: access and recovery never wait for a language fetch.
void i18next.use(initReactI18next).init({
  resources: { en, es }, lng: 'en', fallbackLng: 'en', supportedLngs: ['en', 'es'],
  defaultNS: 'common', returnNull: false, initAsync: false,
  keySeparator: false, nsSeparator: false,
  interpolation: { escapeValue: false }, react: { useSuspense: false },
});
export default i18next;
