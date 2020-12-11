import pandas as pd

df = pd.DataFrame()
df['val'] = [1, 1, 1, 1]
df['added'] = [1, 1, None, None]
df['deleted'] = [1, None, 1, None]
print(df)
df1 = df[df.added==True]
print(df1)

df2=df1[(df1.added==True)|(df1.deleted==True)]
print(df2)
df3=df1[(df1.added==True)&(df1.deleted==True)]
print(df3)
