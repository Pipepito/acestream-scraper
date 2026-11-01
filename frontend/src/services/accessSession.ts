/** Request state lives in memory; login credentials never enter browser storage. */
let csrf = '';
let managed = false;
export const accessSession = {
  csrf: () => csrf,
  managed: () => managed,
  update: (token: string, accounts: boolean) => { csrf = token; managed = accounts; },
};
export const ACCESS_EXPIRED = 'scraper:access-expired';
