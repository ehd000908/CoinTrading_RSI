import tensorflow as tf
import pyupbit
import math
import numpy as np

i = 1000

df = pyupbit.get_ohlcv(ticker="KRW-XRP", interval="minute5", count=2000, period=1)



def makeY(df, i):
    gap = df['close'].iloc[i+1] - df['close'].iloc[i]
    tempY = 1 if gap > 0 else 0
    return tempY

y = []


def scaleDown(df, name, i):
    return round(df[name].iloc[i]/math.pow(10,len(str(int(df[name].iloc[i])))),3)

def makeX(df, i):
    tempX = []
    tempX.append(scaleDown(df, 'open', i))
    tempX.append(scaleDown(df, 'high', i))
    tempX.append(scaleDown(df, 'low', i))
    tempX.append(scaleDown(df, 'close', i))
    tempX.append(scaleDown(df, 'volume', i))
    return tempX

x = []


#인풋 데이터 5개 이므로 shape=(5,)를 대입
inputs = tf.keras.Input(shape=(5,))

# h1 ~ h3은 히든 레이어, 층이 깊을 수록 정확도가 높아질 수 있음
# relu, tanh는 활성화 함수의 종류
h1 = tf.keras.layers.Dense(128, activation='relu')(inputs)
h2 = tf.keras.layers.Dense(128, activation='tanh')(h1)
h3 = tf.keras.layers.Dense(128, activation='relu')(h2)
h4 = tf.keras.layers.Dense(128, activation='tanh')(h3)
h5 = tf.keras.layers.Dense(128, activation='relu')(h4)
h6 = tf.keras.layers.Dense(128, activation='tanh')(h5)

# 값을 0 ~ 1 사이로 표현할 경우 sigmoid 활성화 함수 활용
# 마지막 아웃풋 값은 1개여야 함
outputs = tf.keras.layers.Dense(1, activation='sigmoid')(h3)

# 인풋, 아웃풋 설정을 대입하여 모델 생성 
model = tf.keras.Model(inputs=inputs, outputs=outputs)

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=['accuracy'])

# 인풋/아웃풋 데이터 생성
for i in range(len(df)):
    if i < len(df)-2:
        x.append(makeX(df, i))
        y.append(makeY(df, i))

# 인풋, 아웃풋 데이터를 numpy 포맷으로 대입
# epochs는 학습 반복 횟수
fitInfo = model.fit(np.array(x), np.array(y), epochs=2000)

result = {'accuracy': round(fitInfo.history['accuracy'][-1],2),
          'predict': round(model.predict([makeX(df, -2)])[0][0],2)}

print(result)