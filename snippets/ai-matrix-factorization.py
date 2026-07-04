### Intro
# Libraries: Surprise, LightFM, and implicit


### ALS + SGD

import numpy as np

# Function to generate synthetic user-item interaction matrices
def generate_interaction_matrix(feedback_type='implicit', num_users=100, num_items=50, interaction_density=0.1, rating_scale=(1, 5)):
    np.random.seed(42)  # Ensure reproducible results
    
    # Generate implicit feedback matrix
    if feedback_type == 'implicit':
        # Create a random matrix with values in [0, 1)
        random_matrix = np.random.rand(num_users, num_items)
        # Create a binary interaction matrix based on the defined density
        interaction_matrix = (random_matrix < interaction_density).astype(int)
    # Generate explicit feedback matrix
    elif feedback_type == 'explicit':
        # Start with a matrix of zeros
        interaction_matrix = np.zeros((num_users, num_items))
        # Populate the matrix with random ratings within the specified scale
        for i in range(num_users):
            for j in range(num_items):
                if np.random.rand() < interaction_density:  # Apply density to decide on filling a cell
                    interaction_matrix[i, j] = np.random.randint(rating_scale[0], rating_scale[1] + 1)
    
    return interaction_matrix

# Example of a manually created user-item interaction matrix with explicit feedback
user_item_matrix = np.array([
    [3, 0, 2, 0, 0],
    [0, 0, 4, 5, 2],
    [1, 2, 0, 0, 0],
    [1, 0, 0, 4, 1],
    [0, 2, 3, 0, 0]
])

# Generate synthetic matrices
implicit_matrix = generate_interaction_matrix(feedback_type='implicit', num_users=100, num_items=50, interaction_density=0.1)
explicit_matrix = generate_interaction_matrix(feedback_type='explicit', num_users=100, num_items=50, interaction_density=0.1)

# Display samples from the generated matrices
print("Generated Implicit Feedback Matrix Sample:")
print(implicit_matrix[:5, :5])  # Display a 5x5 sample of the implicit matrix

print("Generated Explicit Feedback Matrix Sample:")
print(explicit_matrix[:5, :5])  # Display a 5x5 sample of the explicit matrix

print("Dummy Manual Matrix for Demonstration:")
print(user_item_matrix)  # Display the manually created matrix

# Generated Implicit Feedback Matrix Sample:
# [[0 0 0 0 0]
# [0 0 0 0 0]
# [1 0 0 0 0]
# [0 0 0 0 0]
# [0 1 0 0 0]]
# Generated Explicit Feedback Matrix Sample:
# [[0. 0. 0. 0. 0.]
# [0. 0. 4. 5. 0.]
# [0. 0. 0. 0. 0.]
# [0. 0. 0. 0. 0.]
# [0. 0. 0. 0. 0.]]
# Dummy Manual Matrix for Demonstration:
# [[3 0 2 0 0]
# [0 0 4 5 2]
# [1 2 0 0 0]
# [1 0 0 4 1]
# [0 2 3 0 0]]

def sgd_als(user_item_matrix, num_factors, learning_rate, regularization, iterations):
    # num_factors: Number of latent factors to use. Higher values can capture more nuanced patterns but risk overfitting.
    # learning_rate: Controls the step size during optimization. Too high can cause overshooting, too low can lead to slow convergence.
    # regularization: Helps prevent overfitting by penalizing large parameter values.
    num_users, num_items = user_item_matrix.shape
    errors = []  # To store RMSE after each iteration
    
    # Initialize user and item latent factor matrices with small random values, 正态分布
    print("init user and item latent factors")
    user_factors = np.random.normal(scale=1./num_factors, size=(num_users, num_factors))
    item_factors = np.random.normal(scale=1./num_factors, size=(num_items, num_factors))
    
    # Iterate over the specified number of iterations
    for iteration in range(iterations):
        total_error = 0
        # Loop through all user-item pairs
        for u in range(num_users):
            # print(f'user = {u}')
            for i in range(num_items):
                #  print(f'item = {i}')
                # Only update factors for user-item pairs with interaction
                if user_item_matrix[u, i] > 0:
                    # Compute the prediction error
                    error = user_item_matrix[u, i] - np.dot(user_factors[u, :], item_factors[i, :].T)
                    total_error += error**2
                    # Update rules for user and item factors
                    user_factors[u, :] += learning_rate * (error * item_factors[i, :] - regularization * user_factors[u, :])
                    item_factors[i, :] += learning_rate * (error * user_factors[u, :] - regularization * item_factors[i, :])
        # Calculate RMSE for current iteration
        rmse = np.sqrt(total_error / np.count_nonzero(user_item_matrix))
        errors.append(rmse)

    return user_factors, item_factors, errors


def predict(user_factors, item_factors):
    """Predict the user-item interactions."""
    return np.dot(user_factors, item_factors.T)


# Example usage parameters
num_factors = 3  # Number of latent factors
learning_rate = 0.001  # Learning rate for SGD
regularization = 0.1  # Regularization parameter
iterations = 10000  # Number of iterations

# Apply SGD ALS
# user_factors, item_factors, errors = sgd_als(user_item_matrix, num_factors, learning_rate, regularization, iterations)
user_factors, item_factors, errors = sgd_als(user_item_matrix, num_factors, learning_rate, regularization, iterations)
# Predict interactions
predictions = predict(user_factors, item_factors)

print("Predictions:")
print(predictions)
# init user and item latent factors
# Predictions:
# [[2.74673304 1.67873889 2.02095291 1.81543743 1.40078986]
#  [2.19166299 1.95915441 3.82886553 4.92874692 1.83125884]
#  [1.01791858 1.81996846 1.30796385 1.05506906 0.69961991]
#  [0.9771647  0.94682205 2.6555658  3.77808443 1.12173388]


import matplotlib.pyplot as plt
plt.plot(errors)
plt.title('SGD ALS Learning Process')
plt.xlabel('Iteration')
plt.ylabel('RMSE')
plt.show()
#  [1.75792289 1.94502747 2.86182183 3.41910276 1.40167863]]