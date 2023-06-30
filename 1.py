import altair as alt
import numpy as np
import pandas as pd

x = np.arange(100)
source = pd.DataFrame({
  'x': x,
  'f(x)': np.sin(x / 5)
})

p1 = alt.Chart(source).mark_line().encode(
    x='x',
    y='f(x)'
)

print(p1.to_html())