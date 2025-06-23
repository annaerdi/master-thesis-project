import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


data = {
    'Simulation': ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08', 'S09', 'S10'],
    'Type': ['AI', 'Human', 'AI', 'Human', 'Human', 'Human', 'AI', 'AI', 'Human', 'AI'],
    'DurationSec': [50, 135, 72, 179, 109, 136, 66, 64, 191, 74],
    'Confidence': [3.84, 3.84, 3.46, 4.0, 3.84, 3.77, 3.54, 3.0, 3.69, 3.77]
}

df = pd.DataFrame(data)

# duration bins
df['DurationCategory'] = pd.cut(df['DurationSec'], bins=[0, 75, 120, 200], labels=['<1:15', '1:15–2:00', '>2:00'])

plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x='DurationCategory', y='Confidence', hue='DurationCategory', palette='muted', legend=False)
sns.stripplot(data=df, x='DurationCategory', y='Confidence', hue='Type', dodge=True, jitter=True, alpha=0.7, marker='o', palette={'AI': 'red', 'Human': 'blue'})
plt.title('Reviewer Confidence vs. Simulation Duration')
plt.xlabel('Simulation Duration')
plt.ylabel('Avg. Confidence Score')
plt.legend(title='Simulation Type', loc='lower right')
plt.tight_layout()
plt.savefig("confidence_duration_boxplot.png", dpi=300)
