const normalizeBrandText = (value: string) => value.toLocaleLowerCase().replace(/[^a-z0-9₹ ]/g, " ").replace(/\s+/g, " ").trim();

const brandAliases: Record<string, string[]> = {
  "AI+": ["ai+", "ai plus"],
  Motorola: ["motorola", "moto"],
  OnePlus: ["oneplus", "one plus"],
  iQOO: ["iqoo", "i qoo"],
};

export function matchBrandName(question: string, brands: string[]): string | null {
  const normalizedQuestion = normalizeBrandText(question);
  const tokens = normalizedQuestion.split(" ").filter(Boolean);
  const matchesAlias = (alias: string) => {
    const normalizedAlias = normalizeBrandText(alias);
    if (!normalizedAlias) return false;
    if (normalizedAlias.includes(" ")) return ` ${normalizedQuestion} `.includes(` ${normalizedAlias} `);
    return tokens.some((token) => token === normalizedAlias || token === `${normalizedAlias}s`);
  };
  return [...brands].sort((a, b) => b.length - a.length).find((brand) => (brandAliases[brand] || [brand]).some(matchesAlias)) || null;
}
