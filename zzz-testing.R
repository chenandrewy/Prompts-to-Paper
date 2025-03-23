library(tidyverse)

p = 0.01
F = 50
b = 0.80
gamma = 10
beta = 0.99

numer = (1-p) + p*F*(1-b)
denom = (1-p) + p*F*(1-b)^(1-gamma)

eret_pct = 100*(1/beta*(numer/denom)-1)

eret_pct

(1-b)^(1-gamma)

approx_eret_pct = 100*(1/beta*(1+p*F*((1-b)-(1-b)^(1-gamma))))

approx_eret_pct
