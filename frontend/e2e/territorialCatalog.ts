export const APPROVED_PARTIES = [
  'ALMIRANTE BROWN',
  'AVELLANEDA',
  'BERAZATEGUI',
  'CAÑUELAS',
  'ESTEBAN ECHEVERRÍA',
  'EZEIZA',
  'FLORENCIO VARELA',
  'LANÚS',
  'LOMAS DE ZAMORA',
  'PRESIDENTE PERÓN',
  'QUILMES',
  'SAN VICENTE',
] as const;

export const TERRITORIAL_AREAS = {
  coverage_version: '2026-11-15',
  coverage_retrieved_on: '2026-11-15',
  areas: [
    { partido: 'ALMIRANTE BROWN', localidades: [
      { localidad: 'GLEW', coverage: 'coverage_unverified' },
    ] },
    { partido: 'AVELLANEDA', localidades: [] },
    { partido: 'BERAZATEGUI', localidades: [
      { localidad: 'BERAZATEGUI', coverage: 'coverage_unverified' },
    ] },
    { partido: 'CAÑUELAS', localidades: [] },
    { partido: 'ESTEBAN ECHEVERRÍA', localidades: [] },
    { partido: 'EZEIZA', localidades: [] },
    { partido: 'FLORENCIO VARELA', localidades: [] },
    { partido: 'LANÚS', localidades: [] },
    { partido: 'LOMAS DE ZAMORA', localidades: [
      { localidad: 'BANFIELD', coverage: 'coverage_unverified' },
    ] },
    { partido: 'PRESIDENTE PERÓN', localidades: [] },
    { partido: 'QUILMES', localidades: [] },
    { partido: 'SAN VICENTE', localidades: [] },
  ],
};
