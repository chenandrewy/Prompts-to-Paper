library(tidyverse)

denom_pre = function(p, b, gamma, beta) {
  return(1-beta*((1-p)))
}

denom_post = function(p, b, gamma, beta) {
  return(1-beta*((1-p)+p*exp(b*gamma)))
}


# make a table of the denominator for a range of values of p and b
p_values = c(0.05, 0.01, 0.005)
b_values = seq(0.2, 0.95, 0.20)

df = expand.grid(p = p_values, b = b_values)

df$denom_pre = denom_pre(df$p, df$b, gamma=2, beta=0.96)
df$denom_post = denom_post(df$p, df$b, gamma=2, beta=0.96)

df_pre = df %>%
  select(p, b, denom_pre) %>%
  pivot_wider(names_from = p, values_from = denom_pre, names_prefix = "p_") %>% 
  print()

df_post = df %>%
  select(p, b, denom_post) %>%
  pivot_wider(names_from = p, values_from = denom_post, names_prefix = "p_") %>% 
  print()