# Test-set comparison (35 questions)

| System | EM | F1 | Evidence recall | All evidence found | Avg latency (s) | Est. cost (USD) | Failures |
|---|---|---|---|---|---|---|---|
| Vector k=5 (baseline) | 0.371 | 0.537 | 0.786 | 0.600 | 1.61 | 0.0063 | 0 |
| Vector k=8 (control) | 0.429 | 0.583 | 0.871 | 0.743 | 1.41 | 0.0084 | 0 |
| Graph only (depth 2) | 0.371 | 0.489 | 0.643 | 0.457 | 1.33 | 0.0038 | 0 |
| Hybrid depth 1 | 0.486 | 0.670 | 0.886 | 0.800 | 1.45 | 0.0066 | 0 |
| Hybrid depth 2 | 0.429 | 0.608 | 0.886 | 0.800 | 1.59 | 0.0071 | 0 |

## By question type

| System | Bridge EM | Bridge F1 | Comparison EM | Comparison F1 |
|---|---|---|---|---|
| Vector k=5 (baseline) | 0.276 | 0.476 | 0.833 | 0.833 |
| Vector k=8 (control) | 0.379 | 0.566 | 0.667 | 0.667 |
| Graph only (depth 2) | 0.276 | 0.417 | 0.833 | 0.833 |
| Hybrid depth 1 | 0.414 | 0.636 | 0.833 | 0.833 |
| Hybrid depth 2 | 0.414 | 0.631 | 0.500 | 0.500 |

## Hybrid depth 2 vs vector k=8 (per question)

Hybrid found all evidence where vector k=8 did not: 6
Vector k=8 found all evidence where hybrid did not: 4
Hybrid answer F1 better by 0.5 or more: 5
Hybrid answer F1 worse by 0.5 or more: 3

### Graph helped (evidence)

- Q: The organization that Nicolae Titulescu served two terms as president was founded on what date?
  gold: 10 January 1920 | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: '10 January 1920' (F1 1.00)
  graph-added paragraphs: ['League of Nations']
- Q: This term about a playwright who lived from 1564-1616 presented what about his works? 
  gold: chronological collection of critical quotations | vector k=8: "Most of his tragedies are designated 'Shakespearean tragedy'" (F1 0.15) | hybrid: 'A chronological collection of critical quotations about his works' (F1 0.77)
  graph-added paragraphs: ['Timeline of Shakespeare criticism']
- Q: In what year was the singer who popularized "I'll Keep the Lovelight Burning" born?
  gold: 1927 | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: '1927' (F1 1.00)
  graph-added paragraphs: ['Patti Page']
- Q: Grown-Ups starred the actor who was best known for which role on  "'Allo 'Allo!"?
  gold: Captain Hans Geering | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: 'Captain Hans Geering' (F1 1.00)
  graph-added paragraphs: ['Vicki Michelle', 'Roger Kitter', 'Grown-Ups']
- Q: Howard Van Doren Shaw was the designer of which 1917 Progressive Era community? 
  gold: Marktown | vector k=8: 'Marktown' (F1 1.00) | hybrid: 'Marktown' (F1 1.00)
  graph-added paragraphs: ['Deerpath Hill Estates', 'Marktown', 'Seven Houses on Lake Shore Drive District']
- Q: What company did Rex Maughan aquire?
  gold: Aloe Vera of America | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: 'Aloe Vera of America' (F1 1.00)
  graph-added paragraphs: ['Forever Living Products']

### Graph hurt (evidence)

- Q: Sadok Sassi played for a national team that made its first World Cup in what year?
  gold: 1978 | vector k=8: '1978' (F1 1.00) | hybrid: 'insufficient evidence' (F1 0.00)
  graph-added paragraphs: []
- Q: whats the famous bavagheet by arun date?
  gold: Shukratara | vector k=8: 'Shukratara' (F1 1.00) | hybrid: 'Shukratara' (F1 1.00)
  graph-added paragraphs: ['Sudha Malhotra']
- Q: Who did Muhummad Ali fight next, in Houston, after the so-called Fight of the Century with Joe Frazier?
  gold: Jimmy Ellis | vector k=8: 'Jimmy Ellis' (F1 1.00) | hybrid: 'insufficient evidence' (F1 0.00)
  graph-added paragraphs: ['George Chuvalo', 'La Voz de Houston']
- Q: What is represented on the cover art of the studio album that includes the song "Speed of Sound"?
  gold: Baudot code | vector k=8: 'A combination of colours and blocks representing the Baudot code' (F1 0.40) | hybrid: 'insufficient evidence' (F1 0.00)
  graph-added paragraphs: []

### Hybrid answer much better

- Q: The organization that Nicolae Titulescu served two terms as president was founded on what date?
  gold: 10 January 1920 | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: '10 January 1920' (F1 1.00)
  graph-added paragraphs: ['League of Nations']
- Q: This term about a playwright who lived from 1564-1616 presented what about his works? 
  gold: chronological collection of critical quotations | vector k=8: "Most of his tragedies are designated 'Shakespearean tragedy'" (F1 0.15) | hybrid: 'A chronological collection of critical quotations about his works' (F1 0.77)
  graph-added paragraphs: ['Timeline of Shakespeare criticism']
- Q: In what year was the singer who popularized "I'll Keep the Lovelight Burning" born?
  gold: 1927 | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: '1927' (F1 1.00)
  graph-added paragraphs: ['Patti Page']
- Q: Grown-Ups starred the actor who was best known for which role on  "'Allo 'Allo!"?
  gold: Captain Hans Geering | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: 'Captain Hans Geering' (F1 1.00)
  graph-added paragraphs: ['Vicki Michelle', 'Roger Kitter', 'Grown-Ups']
- Q: What company did Rex Maughan aquire?
  gold: Aloe Vera of America | vector k=8: 'insufficient evidence' (F1 0.00) | hybrid: 'Aloe Vera of America' (F1 1.00)
  graph-added paragraphs: ['Forever Living Products']

### Hybrid answer much worse

- Q: Sadok Sassi played for a national team that made its first World Cup in what year?
  gold: 1978 | vector k=8: '1978' (F1 1.00) | hybrid: 'insufficient evidence' (F1 0.00)
  graph-added paragraphs: []
- Q: Who did Muhummad Ali fight next, in Houston, after the so-called Fight of the Century with Joe Frazier?
  gold: Jimmy Ellis | vector k=8: 'Jimmy Ellis' (F1 1.00) | hybrid: 'insufficient evidence' (F1 0.00)
  graph-added paragraphs: ['George Chuvalo', 'La Voz de Houston']
- Q: Which professional tennis player was born first, Lucie Hradecká or Raffaella Reggi?
  gold: Raffaella Reggi | vector k=8: 'Raffaella Reggi' (F1 1.00) | hybrid: 'Lucie Hradecká' (F1 0.00)
  graph-added paragraphs: ['František Čermák', 'Andrea Hlaváčková', 'Praha-Smíchov railway station']
