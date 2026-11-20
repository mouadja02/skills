// Shared by the classic browser scripts and the dependency-free MCP server.
(() => {
  const stopWords = new Set("a an and are as at be by for from how in is it me of on or that the to use what when with you".split(" "));
  const aliases = [
    ["k8s", "kubernetes"], ["pr", "pull request"], ["tdd", "test driven development"],
    ["postgres", "postgresql"], ["slides", "presentation", "powerpoint", "pptx"],
    ["python unit tests", "pytest"], ["speed up", "optimize", "optimization"],
    ["slow database queries", "sql performance", "query optimization"],
  ];

  function tokens(text) {
    return (String(text ?? "").normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase()
      .match(/[\p{L}\p{N}]+(?:[+#]{1,2})?/gu) || [])
      .filter(word => !stopWords.has(word))
      .map(word => {
        if (/^[a-z]+$/.test(word) && word.length > 4 && word.endsWith("ies")) return word.slice(0, -3) + "y";
        if (/^[a-z]+$/.test(word) && word.length > 3 && /[^su]s$/.test(word)) return word.slice(0, -1);
        return word;
      });
  }

  const aliasConcepts = aliases.map(group => group.map(tokens));

  function queryConcepts(query, useSynonyms) {
    const concepts = [];
    const words = tokens(query);
    for (let i = 0; i < words.length;) {
      const groups = useSynonyms ? aliasConcepts : [];
      let best = null;
      for (const group of groups) {
        for (const phrase of group) {
          if ((!best || phrase.length > best.length) && phrase.every((word, offset) => words[i + offset] === word)) {
            best = { group, length: phrase.length };
          }
        }
      }
      concepts.push(best ? best.group : [[words[i]]]);
      i += best?.length || 1;
    }
    return concepts;
  }

  function createRanker(skills, index = {}, { synonyms = true, expansion = false } = {}) {
    const documents = skills.map(skill => {
      const extra = index[skill.install_path] || {};
      const weights = new Map();
      const fields = [
        [skill.name, 12], [skill.install_path, 8], [skill.category, 3], [skill.description, 4],
        [extra.use, 3], [extra.headers, 2],
        [[skill.license, skill.attribution, skill.source].join(" "), 2],
      ];
      for (const [field, weight] of fields) {
        for (const word of tokens(field)) weights.set(word, Math.max(weight, weights.get(word) || 0));
      }
      return { skill, weights, expanded: new Set(expansion ? extra.expand || [] : []) };
    });
    const frequency = new Map();
    for (const { weights } of documents) {
      for (const word of weights.keys()) frequency.set(word, (frequency.get(word) || 0) + 1);
    }
    const corpusSize = documents.length;

    function scorePhrase(phrase, weights, expanded) {
      let score = 0;
      for (const word of phrase) {
        const weight = weights.get(word) || (expanded.has(word) ? 1 : 0);
        if (!weight) return 0;
        const occurrences = frequency.get(word) || 0;
        score += weight * Math.log(1 + (corpusSize - occurrences + 0.5) / (occurrences + 0.5));
      }
      return phrase.length ? score / phrase.length : 0;
    }

    return function rank(query, { keywords = [], filter } = {}) {
      const concepts = queryConcepts(query, synonyms);
      const related = keywords.map(tokens).filter(words => words.length);
      if (!concepts.length && !related.length) return [];
      const phrase = tokens(query).join(" ");
      const results = [];
      for (const { skill, weights, expanded } of documents) {
        if (filter && !filter(skill)) continue;
        const scores = concepts.map(group => Math.max(...group.map(words => scorePhrase(words, weights, expanded))));
        const keywordScore = Math.max(0, ...related.map(words => scorePhrase(words, weights, expanded)));
        if ((!scores.length || scores.includes(0)) && !keywordScore) continue;
        const exact = phrase && [skill.name, skill.install_path].some(value => tokens(value).join(" ") === phrase);
        const score = scores.reduce((total, value) => total + value, 0) + 0.5 * keywordScore + (exact ? 40 : 0);
        results.push({ skill, score });
      }
      return results.sort((a, b) => b.score - a.score || a.skill.install_path.localeCompare(b.skill.install_path, "en"));
    };
  }

  globalThis.skillCatalogSearch = { tokens, createRanker };
})();
