---
name: Infographic Definition
about: Provide description and implementation details
title: 'Widget: '
labels: infographics-API
assignees: ''
---

# new\_infographic

**Name** Internal issue description \(e.g. "query for pedestrian injury types at a specific street"\).

**Title** Infographic name to be used in FE.

**Visualization** Sample graphic image of the diagram that will be displayed by FE.

**Visualization explanation** Explain visualization content.

**Use case** When this infographic should be displayed

**SQL query** Sql clause and usage guidance. In addition to query, detail which parameters should be modified when executing it and which output fields are language specific When creating the query and filtering CBS data - it's better to use the numeric values of the categorical fields \(accident\_severity = 1 is better than accident\_severity\_hebrew = 'תאונה קטלנית'\). For code redeablity - one can create constants and dictionaries.

**Additional context**

* Definition will be used by BE team to generate a Json response to FE
* Definition will be provided by Data team, after internal review
* Definition will be written in English and should use language agnostic definitions and data structures 

  \(e.g. SQL columns\) as much as possible.

