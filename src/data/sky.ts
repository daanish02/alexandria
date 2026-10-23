// The night sky drawn behind the graph: real star positions for one moment and one place.
// The sky is computed in the browser from public/stars.json (see scripts/build-stars.mjs).

export interface Place {
  name: string;
  /** degrees north */
  lat: number;
  /** degrees east */
  lon: number;
}

export const sky = {
  /** ISO date */
  date: '2002-05-10',
  /** local mean solar time, in hours (22 = 10 pm) */
  localHour: 22,
  place: { name: 'Hyderabad, India', lat: 17.385, lon: 78.4867 } as Place,
};
