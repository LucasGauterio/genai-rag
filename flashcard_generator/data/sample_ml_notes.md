# Machine Learning Fundamentals

A comprehensive guide to core machine learning concepts.

## Introduction to Machine Learning

Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. The fundamental idea is that machines can identify patterns in data and make decisions with minimal human intervention.

### Types of Machine Learning

There are three main types of machine learning:

1. **Supervised Learning**: The algorithm learns from labeled training data, making predictions based on that data. Examples include classification and regression tasks.

2. **Unsupervised Learning**: The algorithm finds hidden patterns in unlabeled data. Common techniques include clustering and dimensionality reduction.

3. **Reinforcement Learning**: The algorithm learns by interacting with an environment, receiving rewards or penalties for actions. Used in game playing, robotics, and autonomous systems.

## Supervised Learning

### Linear Regression

Linear regression is a statistical method used to model the relationship between a dependent variable and one or more independent variables. The model assumes a linear relationship:

```
y = mx + b
```

Where:
- `y` is the predicted value
- `m` is the slope (weight)
- `x` is the input feature
- `b` is the bias (intercept)

The goal is to find the optimal values of m and b that minimize the prediction error.

### Gradient Descent

Gradient Descent is an optimization algorithm used to minimize the loss function by iteratively adjusting the model parameters. The algorithm works by:

1. Starting with random parameter values
2. Computing the gradient (derivative) of the loss function
3. Updating parameters in the opposite direction of the gradient
4. Repeating until convergence

The update rule is:
```
θ = θ - α * ∇J(θ)
```

Where α (alpha) is the learning rate, which controls how large the steps are.

### Classification

Classification is a supervised learning task where the goal is to predict categorical labels. Common algorithms include:

- **Logistic Regression**: Despite its name, used for binary classification using the sigmoid function
- **Decision Trees**: Tree-structured models that make decisions based on feature values
- **Support Vector Machines (SVM)**: Find the optimal hyperplane that separates classes
- **Neural Networks**: Multi-layer perceptrons that can learn complex decision boundaries

## Neural Networks

### Basic Architecture

A neural network consists of interconnected nodes (neurons) organized in layers:

1. **Input Layer**: Receives the raw input features
2. **Hidden Layers**: Perform intermediate computations
3. **Output Layer**: Produces the final prediction

Each connection has an associated weight, and each neuron applies an activation function to its weighted inputs.

### Activation Functions

Activation functions introduce non-linearity into the network. Common choices include:

- **ReLU (Rectified Linear Unit)**: f(x) = max(0, x) - Most popular for hidden layers
- **Sigmoid**: f(x) = 1/(1 + e^(-x)) - Used for binary classification output
- **Softmax**: Normalizes outputs to probability distribution - Used for multi-class classification
- **Tanh**: f(x) = (e^x - e^(-x))/(e^x + e^(-x)) - Outputs between -1 and 1

### Backpropagation

Backpropagation is the algorithm used to train neural networks. It works by:

1. Forward pass: Compute predictions
2. Calculate loss between predictions and actual values
3. Backward pass: Compute gradients using the chain rule
4. Update weights using gradient descent

This allows the network to learn which weights need adjustment to reduce error.

## Overfitting and Regularization

### Overfitting

Overfitting occurs when a model learns the training data too well, including its noise and outliers, leading to poor generalization on new data. Signs of overfitting include:

- High accuracy on training data
- Low accuracy on validation/test data
- Model captures noise rather than underlying patterns

### Regularization Techniques

To prevent overfitting:

1. **L1 Regularization (Lasso)**: Adds absolute value of weights to loss function, can lead to sparse models
2. **L2 Regularization (Ridge)**: Adds squared weights to loss function, prevents weights from becoming too large
3. **Dropout**: Randomly "drops" neurons during training, forcing the network to learn redundant representations
4. **Early Stopping**: Stop training when validation error starts increasing

## Model Evaluation

### Metrics

Different metrics are appropriate for different tasks:

**For Classification:**
- **Accuracy**: Proportion of correct predictions
- **Precision**: Of predicted positives, how many are actually positive
- **Recall**: Of actual positives, how many were predicted correctly
- **F1 Score**: Harmonic mean of precision and recall

**For Regression:**
- **Mean Squared Error (MSE)**: Average of squared differences
- **Root Mean Squared Error (RMSE)**: Square root of MSE
- **Mean Absolute Error (MAE)**: Average of absolute differences
- **R² Score**: Proportion of variance explained by the model

### Cross-Validation

Cross-validation is a technique to assess model performance by training and testing on different subsets of data. K-fold cross-validation:

1. Split data into K equal parts (folds)
2. Train on K-1 folds, test on remaining fold
3. Repeat K times, each time using a different fold for testing
4. Average the results for final evaluation

This provides a more robust estimate of model performance than a single train-test split.
