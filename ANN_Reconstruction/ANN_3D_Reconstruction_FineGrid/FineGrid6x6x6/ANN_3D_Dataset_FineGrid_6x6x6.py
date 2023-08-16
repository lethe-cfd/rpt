import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from matplotlib import pyplot
from sklearn.preprocessing import MinMaxScaler
import re
import csv
from keras import backend as K

# Number of training points
NUM_TP=291710###

# Feed file content
Feed=np.zeros([NUM_TP,10])

# File for the number of counts
filename_counts = 'interpolaited_counts_all_dataset3D4.txt'
data_counts = np.loadtxt(filename_counts, delimiter='\t')

for i in range(7):
    Feed[:,i] = data_counts[0:NUM_TP, i]

# File for the position x and y
filename_pos = 'x_y_robot_position_dataset3D4.txt'
data_pos = np.loadtxt(filename_pos, delimiter=',')


Feed[:,7] = (data_pos[0:NUM_TP, 0]-570.004)/1000
Feed[:,8] = (data_pos[0:NUM_TP, 1]+169.990)/1000
Feed[:,9] = (data_pos[0:NUM_TP, 2]-840.497)/1000

# Write the counts and position on a text file
with open("Feed.txt", "w") as file_output: 
    file_output.truncate(0)
    for row in Feed:
        line = '\t'.join([str(item) for item in row])
        file_output.write(f'{line}\n')


#Define input features 
Count1= keras.Input(shape=(1,), name="Count1")
Count2= keras.Input(shape=(1,), name="Count2")
Count3= keras.Input(shape=(1,), name="Count3")
Count4= keras.Input(shape=(1,), name="Count4")
Count5= keras.Input(shape=(1,), name="Count5")
Count6= keras.Input(shape=(1,), name="Count6")
Count7= keras.Input(shape=(1,), name="Count7")

# Joining strings together end-to-end to create a new string to feed the model
# The new string is input layer
x = layers.concatenate([Count1,Count2,Count3,Count4,Count5,Count6,Count7])


#Define the hidden layers
hidden1 = layers.Dense(256, activation='tanh')(x)
hidden2 = layers.Dense(128, activation='tanh')(hidden1)
hidden3 = layers.Dense(64, activation='tanh')(hidden2)
hidden4 = layers.Dense(32, activation='tanh')(hidden3)
hidden5 = layers.Dense(16, activation='tanh')(hidden4)

X = layers.Dense(1,activation='linear', name="xx")(hidden5)
Y = layers.Dense(1,activation='linear', name="yy")(hidden5)
Z = layers.Dense(1,activation='linear', name="zz")(hidden5)

model = keras.Model(inputs=[Count1,Count2,Count3,Count4,Count5,Count6,Count7],outputs=[X, Y, Z],)


keras.backend.set_epsilon(1)
model.compile(
    optimizer='Adam',
    loss=['mse', 'mse','mse'],
    loss_weights=[1.0, 1.0,1.0],
    metrics=['MAE','mean_absolute_percentage_error']   
)

# Define the learning rate
LR=0.001
K.set_value(model.optimizer.learning_rate,LR)

pd_dat = pd.read_csv('Feed.txt', delimiter='\t')

# Extract the values from the dataframe
dataset = pd_dat.values

#Normalizing the input counts
X_raw=dataset[:,:7]
scaler_X = MinMaxScaler()
scaler_X.fit(X_raw)
X_scale= scaler_X.transform(X_raw)


X_train, X_test, Y_train, Y_test = train_test_split(X_scale[:,:7],dataset[:,7:], test_size=0.2)


count1_train, count2_train, count3_train, count4_train, count5_train, count6_train, count7_train = np.transpose(X_train)
count1_test, count2_test, count3_test, count4_test, count5_test, count6_test, count7_test  = np.transpose(X_test)

with open('test.txt','w') as file:
	for i in range(len(Y_train)):
		file.write(str(Y_train[i,:])+'\n')
	
x_train, y_train, z_train = Y_train[:,0], Y_train[:,1], Y_train[:,2]
x_test, y_test, z_test = Y_test[:,0], Y_test[:,1], Y_test[:,2]


inputs_train=[count1_train, count2_train, count3_train, count4_train, count5_train, count6_train, count7_train]
outputs_train=[x_train, y_train, z_train]


history=model.fit(inputs_train,outputs_train,
                 validation_split=0.2,
                 epochs=20000,
                 batch_size=20000,
                 )
print(history.history)


result=model.evaluate([count1_test, count2_test, count3_test, count4_test, count5_test, count6_test, count7_test],[x_test,y_test,z_test],verbose=2)
print(result)


pyplot.subplot(211)
pyplot.title('Loss RUN 4')
plt.semilogy(history.history['loss'], label='train')
plt.semilogy(history.history['val_loss'], label='validation')
plt.xscale("log")
pyplot.legend()


# In[13]:

# Array of the counts used for the prediction of the spiral
Pred = data_counts[-9000:-1, :7] 

X_pre=Pred
scaler_X_pre = MinMaxScaler()
scaler_X_pre.fit(X_pre)
X_scale_pre= scaler_X.transform(X_pre)
count1_pre, count2_pre, count3_pre, count4_pre, count5_pre, count6_pre, count7_pre=np.transpose(X_scale_pre)
prediction=model.predict([count1_pre, count2_pre, count3_pre, count4_pre, count5_pre, count6_pre, count7_pre])

# Real position of the robot during the spiral
x_real=(data_pos[-9000:-1, 0]-570.004)/1000
y_real=(data_pos[-9000:-1, 1]+169.990)/1000  
z_real=(data_pos[-9000:-1, 2]-840.497)/1000  

ax=plt.figure().add_subplot(projection='3d')
ax.plot(x_real, y_real, z_real, label='Real')


# Convert the data to a NumPy array
x_pred=np.zeros(len(x_real))
y_pred=np.zeros(len(y_real))
z_pred=np.zeros(len(z_real))


for i in range(len(x_pred)):
    x_pred[i]=prediction[0][i][0]
    y_pred[i]=prediction[1][i][0]
    z_pred[i]=prediction[2][i][0]
    
    
ax.plot(x_pred,y_pred, z_pred,label='Prediction')
ax.legend()
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')


Erreur_x=np.abs(x_pred-x_real)
MAE_x=Erreur_x.mean()

Erreur_y=np.abs(y_pred-y_real)
MAE_y=Erreur_y.mean()

Erreur_z=np.abs(z_pred-z_real)
MAE_z=Erreur_z.mean()

print('MAE_x_spiral = ', MAE_x, '\n', 'MAE_y_spiral', MAE_y,'\n', 'MAE_z_spiral', MAE_z)

# In[15]: 
	
# Lign pattern x

plt.figure()
plt.plot(Feed[5200:5700,7],Feed[5200:5700,8],label='Real')
plt.ylabel('y (m)')
plt.xlabel('x (m)')


X_pre=Feed[5200:5700,:7]
scaler_X_pre = MinMaxScaler()
scaler_X_pre.fit(X_pre)
X_scale_pre= scaler_X.transform(X_pre)
count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre=np.transpose(X_scale_pre)
prediction=model.predict([count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre])

plt.plot(prediction[0][:],prediction[1][:],label='Pred')
plt.title('End pattern')
plt.legend()

sampling_time=np.arange(500)

plt.figure()
plt.plot(sampling_time,Feed[5200:5700,7],label='Real')
plt.plot(sampling_time,prediction[0][:],label='Pred')
plt.xlabel('Sampling time for the line')
plt.ylabel('x')
plt.legend()


ERREURLAG=prediction[0][:]-Feed[5200:5700,7]
ERREURLAG=ERREURLAG.mean()
print('\n Erreur lag x : ', ERREURLAG)



# Grid

plt.figure()
plt.plot(Feed[25000:60000,7],Feed[25000:60000,8],label='Real')
plt.ylabel('y (m)')
plt.xlabel('x (m)')


X_pre=Feed[25000:60000,:7]
scaler_X_pre = MinMaxScaler()
scaler_X_pre.fit(X_pre)
X_scale_pre= scaler_X.transform(X_pre)
count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre=np.transpose(X_scale_pre)
prediction=model.predict([count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre])

plt.plot(prediction[0][:],prediction[1][:],label='Pred')
plt.title('Grid pattern')
plt.legend()

x_pred=np.zeros(len(Feed[25000:60000,7]))
y_pred=np.zeros(len(Feed[25000:60000,8]))

for i in range(len(x_pred)):
    x_pred[i]=prediction[0][i][0]
    y_pred[i]=prediction[1][i][0]

Erreur_x=np.abs(x_pred-Feed[25000:60000,7])
MAE_x=Erreur_x.mean()

Erreur_y=np.abs(y_pred-Feed[25000:60000,8])
MAE_y=Erreur_y.mean()

print('MAE_x_grid1 = ', MAE_x, '\n', 'MAE_y_grid1', MAE_y)


# Grid

plt.figure()
plt.plot(Feed[125000:160000,7],Feed[125000:160000,8],label='Real')
plt.ylabel('y (m)')
plt.xlabel('x (m)')


X_pre=Feed[125000:160000,:7]
scaler_X_pre = MinMaxScaler()
scaler_X_pre.fit(X_pre)
X_scale_pre= scaler_X.transform(X_pre)
count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre=np.transpose(X_scale_pre)
prediction=model.predict([count1_pre, count2_pre, count3_pre,count4_pre, count5_pre, count6_pre, count7_pre])

plt.plot(prediction[0][:],prediction[1][:],label='Pred')
plt.title('Grid pattern')
plt.legend()

x_pred=np.zeros(len(Feed[125000:160000,7]))
y_pred=np.zeros(len(Feed[125000:160000,8]))

for i in range(len(x_pred)):
    x_pred[i]=prediction[0][i][0]
    y_pred[i]=prediction[1][i][0]

Erreur_x=np.abs(x_pred-Feed[125000:160000,7])
MAE_x=Erreur_x.mean()

Erreur_y=np.abs(y_pred-Feed[125000:160000,8])
MAE_y=Erreur_y.mean()

print('MAE_x_grid2 = ', MAE_x, '\n', 'MAE_y_grid2', MAE_y)


plt.show()

