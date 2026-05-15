function excludeSourceMapLoader(config, pattern) {
  const rules = config.module && config.module.rules ? config.module.rules : [];

  for (const rule of rules) {
    if (Array.isArray(rule.oneOf)) {
      for (const oneOfRule of rule.oneOf) {
        if (oneOfRule.loader && oneOfRule.loader.includes('source-map-loader')) {
          oneOfRule.exclude = Array.isArray(oneOfRule.exclude)
            ? [...oneOfRule.exclude, pattern]
            : oneOfRule.exclude
              ? [oneOfRule.exclude, pattern]
              : [pattern];
        }
      }
    }

    if (rule.loader && rule.loader.includes('source-map-loader')) {
      rule.exclude = Array.isArray(rule.exclude)
        ? [...rule.exclude, pattern]
        : rule.exclude
          ? [rule.exclude, pattern]
          : [pattern];
    }
  }

  return config;
}

module.exports = {
  webpack: {
    configure: (config) => excludeSourceMapLoader(config, /[\\/]node_modules[\\/]@mui[\\/]x-charts[\\/]/),
  },
};