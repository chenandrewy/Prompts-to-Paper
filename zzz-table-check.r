rm(list = ls())
library(tidyverse)


# formula
# \mathbb{E}[R_{t+1}] = (1 - \pi) + \pi e^{-b} + \left( \frac{\frac{1}{\beta} - \left[ (1 - \pi) + \pi e^{-b(1 - \gamma)} \right]}{(1 - \pi) + \pi F e^{-b(1 - \gamma)}} \right) \cdot \left[ (1 - \pi) + \pi F e^{-b} \right]

p = 0.01
b = 0.90
gamma = 2
beta = 0.98

part1 = (1 - p) + p * exp(-b)
part2 = (1 / beta) - ((1 - p) + p * exp(-b * (1 - gamma)))
part3 = ((1 - p) + p * F * exp(-b * (1 - gamma)))
part4 = ((1 - p) + p * F * exp(-b))

ER = part1 + part2 * part3 / part4

ER

calc_ER_pct = function(p, b, gamma, beta, F) {
  part1 = (1 - p) + p * exp(-b)
  part2 = (1 / beta) - ((1 - p) + p * exp(-b * (1 - gamma)))
  part3 = ((1 - p) + p * F * exp(-b * (1 - gamma)))
  part4 = ((1 - p) + p * F * exp(-b))
  ER = part1 + part2 * part3 / part4
  ER_pct = (ER - 1) * 100
  return(ER_pct)
}

# evaluate ER for different values of p and b. small table, 4x4

p_values = c(0.001, 0.01, 0.05, 0.1, 0.2)
b_values = c(0.2, 0.4, 0.6, 0.8, 0.95)
gamma = 2
beta = 0.98
F = 100

# create a data frame with all combinations
df = expand.grid(p = p_values, b = b_values)

# calculate ER for each combination
df$ER_pct = calc_ER_pct(df$p, df$b, gamma, beta, F)

# make wide
df = df %>%
  pivot_wider(names_from = p, values_from = ER_pct, names_prefix = "p_")

# print the data frame
print(df)

# simpler formula
# \mathbb{E}[R] = \frac{(1 - \pi) + \pi F e^{-b}}{\beta \left[ (1 - \pi) + \pi F e^{b(\gamma - 1)} \right]}

calc_ER_pct2 = function(p, b, gamma, beta, F) {
  part1 = (1 - p) + p * F * exp(-b)
  part2 = beta * ((1 - p) + p * F * exp(b * (gamma - 1)))
  ER_pct = (part1 / part2 - 1) * 100
  return(ER_pct)
}

# evaluate ER for different values of p and b. small table, 4x4

# create a data frame with all combinations
df2 = expand.grid(p = p_values, b = b_values)

# calculate ER for each combination
df2$ER_pct = calc_ER_pct2(df2$p, df2$b, gamma, beta, F)

# make wide
df2 = df2 %>%
  pivot_wider(names_from = p, values_from = ER_pct, names_prefix = "p_")

# print the data frame
print(df2)









