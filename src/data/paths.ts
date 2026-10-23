// Curated reading orders, added only once a cluster of about five notes earns one.
// notes are note slugs, in reading order.

export interface Path {
  id: string;
  title: string;
  notes: string[];
}

export const paths: Path[] = [];
