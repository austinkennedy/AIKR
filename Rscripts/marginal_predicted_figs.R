rm(list=ls())
options(scipen=999)

library(yaml)
library(tidyverse)
library(fixest)
library(margins)
library(data.table)
library(sandwich)
library(car)
library(ggpubr)

#load configuration file
config <- yaml.load_file('./Rscripts/r_config.yaml')

volumes <- read.csv(paste(config$temporary_path, 'volumes_scores.csv', sep = '/'))

#Create years and bins, set global params
years <- seq(1510, 1890, by = 1)
min_year <- 1600
interval <- 50
bins <- seq(min_year + (interval/2), 1900 - (interval/2), by = interval)

#Merge volumes to closest bin
a = data.table(Value=volumes$Year) #Extract years
a[,merge:=Value] #Give data.table something to merge on
b = data.table(Value = bins)
b[,merge:=Value]
setkeyv(a, c('merge')) #Sort for quicker merge
setkeyv(b, c('merge'))
rounded = b[a, roll = 'nearest'] #Merge to nearest bin
rounded <- distinct(rounded) #Get distinct values for easier merge to 'volumes'

volumes <- merge(volumes, rounded, by.x = "Year", by.y = "merge")
#Remove unnecessary column
volumes <- volumes %>%
  subset(select = -c(i.Value)) %>%
  rename(bin = Value)

#Drop obs before 1600

volumes <- volumes %>%
  filter(Year > min_year)

#Regressions
reference = min(bins)

category_religion <- config$category_names[1]
category_flexible <- config$category_names[2]
category_science <- config$category_names[3]

#fix special case
if (category_flexible == 'Political Economy') {
  category_flexible <- 'Political.Economy'
}

# if ("Political Economy" %in% colnames(volumes)) {
#   volumes <- volumes %>%
#     rename(Political.Economy = `Political Economy`)
# }

print(names(volumes))

progress_var <- 'progress_main_percentile'

# model <- feols(
#     .[progress_var] ~
#     .[category_science] +
#     .[category_flexible] +
#     .[category_science]*.[category_flexible] +
#     .[category_science]*.[category_religion] +
#     .[category_religion]*.[category_flexible] +
#     i(bin, .[category_science], ref = reference) +
#     i(bin, .[category_flexible], ref = reference) +
#     i(bin, .[category_science]*.[category_religion], ref = reference) +
#     i(bin, .[category_science]*.[category_flexible], ref = reference) +
#     i(bin, .[category_flexible]*.[category_religion], ref = reference) +
#     i(bin, ref = reference) -
#     .[category_religion] +
#     Year,
#     data = volumes,
#     cluster = c('Year')
# )

# print(summary(model))

#rewrite formula to get marginal effects

volumes$bin <- as.factor(volumes$bin)#as factor for easier regression

bins <- as_factor(bins)#gives 'margins' input values

model_formula <- as.formula(paste0(
  progress_var, " ~ ",
  category_religion, "*",
  category_science, "*bin + ",
  category_religion, "*",
  category_flexible, "*bin + ",
  category_science, "*",
  category_flexible, "*bin - ",
  category_religion, " - ",
  category_religion, "*bin + ",
  category_flexible, " + bin + Year"
))

model_marginal_predicted <- lm(model_formula, data = volumes)
print(summary(model_marginal_predicted))

#feed in column names dynamically
get_marginal_science <- function(model, science, religion, flexible){
  cluster = vcovCL(model, cluster = ~Year)

  at <- list()
  at[[category_science]] <- science
  at[[category_religion]] <- religion
  at[[category_flexible]] <- flexible
  at[['bin']] <- bins

  tmp <- model %>%
    margins(
      variables = paste(category_science),
      at = at,
      vcov = cluster
    ) %>%
    summary()
  
  return(tmp)
}

print("Calculating Marginal Effects, may take a while")

s100_m <- get_marginal_science(model = model_marginal_predicted, science = 1, religion = 0, flexible = 0)
s50r50_m <- get_marginal_science(model = model_marginal_predicted, science = 0.5, religion = 0.5, flexible = 0)
s50f50_m <- get_marginal_science(model = model_marginal_predicted, science = 0.5, religion = 0, flexible = 0.5)
thirds_m <- get_marginal_science(model = model_marginal_predicted, science = 1/3, religion = 1/3, flexible = 1/3)
r50f50_m <- get_marginal_science(model = model_marginal_predicted, science = 0, religion = 0.5, flexible = 0.5)

s100_m$label <- paste0("100% ", category_science)
s50r50_m$label <- paste0("50% ", category_science, " 50% ", category_religion)
s50f50_m$label <- paste0("50% ", category_science, " 50% ", category_flexible)
thirds_m$label <- "1/3 Each"
r50f50_m$label <- paste0("50% ", category_religion, " 50% ", category_flexible)

s100_m$bins <- bins
s50r50_m$bins <- bins
s50f50_m$bins <- bins
thirds_m$bins <- bins
r50f50_m$bins <- bins

marg <- rbind(s100_m, s50r50_m, s50f50_m, thirds_m, r50f50_m)

#export/import since it takes forever

write.csv(marg, paste(config$output_path, 'marginal_effects.csv', sep = ''))
marg <- read.csv(paste(config$output_path, 'marginal_effects.csv', sep = ''))

marg$bin <- as.numeric(as.character(marg$bin))

marginal_fig <- ggplot(marg, aes(x = bin, y = AME, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(y = AME, ymin = lower, ymax = upper, fill = label), alpha = 0.2) +
  labs(title = "Marginal Effects", x = "Year", y = "Value") +
  # scale_x_discrete(breaks = c(1600, 1700, 1800, 1900)) +
  theme_light() +
  theme(legend.position = "none")

path <- paste(config$output_path, 'regression_figures/', sep='')


if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)

  print('directory created')
}else{
  print("dir exists")
}

ggsave(paste(path, '/marginal_effects.png', sep=''), width = 5.5)

#Predicted Values
bins_numeric <- as.numeric(levels(bins))

pred <- function(lm, sci, rel, flex){
  cluster = vcovCL(lm, cluster = ~Year)

  data_list <- list()
  data_list[[category_science]] <- sci
  data_list[[category_religion]] <- rel
  data_list[[category_flexible]] <- flex
  data_list[["bin"]] <- bins
  data_list[["Year"]] <- bins_numeric

  data <- as.data.frame(data_list)
  prediction <- Predict(lm, newdata = data, interval = "confidence", se.fit =TRUE, vcov = cluster)
  fit <- data.frame(prediction$fit)
  return(fit)
}

s100_p <- pred(lm = model_marginal_predicted, sci = 1, rel = 0, flex = 0)
s50r50_p <- pred(lm = model_marginal_predicted, sci = 0.5, rel = 0.5, flex = 0)
s50f50_p <- pred(lm = model_marginal_predicted, sci = 0.5, rel = 0, flex = 0.5)
thirds_p <- pred(lm = model_marginal_predicted, sci = 1/3, rel = 1/3, flex = 1/3)
r50f50_p <- pred(lm = model_marginal_predicted, sci = 0, rel = 0.5, flex = 0.5)

s100_p$label <- paste0("100% ", category_science)
s50r50_p$label <- paste0("50% ", category_science, " 50% ", category_religion)
s50f50_p$label <- paste0("50% ", category_science, " 50% ", category_flexible)
thirds_p$label <- "1/3 Each"
r50f50_p$label <- paste0("50% ", category_religion, " 50% ", category_flexible)

s100_p$bin <- bins
s50r50_p$bin <- bins
s50f50_p$bin <- bins
thirds_p$bin <- bins
r50f50_p$bin <- bins

predicted <- rbind(s100_p, s50r50_p, s50f50_p, thirds_p, r50f50_p)

predicted$bin <- as.numeric(as.character(predicted$bin))

predicted_fig <- ggplot(predicted, aes(x = bin, y = fit, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(y = fit, ymin = lwr, ymax = upr, fill = label), alpha = 0.2) +
  labs(title = "Predicted Values", x = "Year", y = "Value") +
  theme_light()


ggsave(paste(path, '/predicted_values.png', sep=''), width = 8)

figure <- ggarrange(marginal_fig, predicted_fig,
                    labels = c("A", "B"),
                    ncol = 2, nrow =1,
                    widths = c(5.5,8))

ggsave(paste(path, '/marginal_predicted_combined.png', sep=''), width = 13.5)