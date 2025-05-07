rm(list=ls())
options(scipen=999)

setwd("E:/grad_school/research/AIKR")

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

output_folder <- config$output_path

#Create years and bins, set global params
years <- seq(1510, 1890, by = 1)
min_year <- config$min_regression_year
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

# progress_vars <- list('progress_main_percentile', 'progress_original_percentile', 'progress_secondary_percentile')
progress_vars <- list('progress_main_percentile')

for (progress_var in progress_vars){
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

# volumes$bin <- as.factor(volumes$bin)#as factor for easier regression

volumes$bin <- factor(volumes$bin)

bins <- as_factor(bins)#gives 'margins' input values

# model_formula <- as.formula(paste0(
#   progress_var, " ~ ",
#   category_religion, "*",
#   category_science, "*bin + ",
#   category_religion, "*",
#   category_flexible, "*bin + ",
#   category_science, "*",
#   category_flexible, "*bin - ",
#   category_religion, " - ",
#   category_religion, "*bin + ",
#   category_flexible, " + bin + Year"
# ))


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
  category_flexible, " + bin"
))

model_marginal_predicted <- lm(model_formula, data = volumes)
print(summary(model_marginal_predicted))

path <- paste(config$output_path, 'regression_figures/', progress_var, sep='')


if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)

  print('directory created')
}else{
  print("dir exists")
}

#Predicted Values
bins_numeric <- as.numeric(levels(bins))

pred <- function(lm, sci, rel, flex){
  cluster = vcovCL(lm, cluster = ~Year)

  data_list <- list()
  data_list[[category_science]] <- sci
  data_list[[category_religion]] <- rel
  data_list[[category_flexible]] <- flex
  data_list[["bin"]] <- bins
  # data_list[["Year"]] <- bins_numeric

  data <- as.data.frame(data_list)
  prediction <- Predict(lm, newdata = data, interval = "confidence", se.fit =TRUE, vcov = cluster)
  # return(prediction)
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

print(predicted)

predicted$bin <- as.numeric(as.character(predicted$bin))

predicted_fig <- ggplot(predicted, aes(x = bin, y = fit, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(y = fit, ymin = lwr, ymax = upr, fill = label), alpha = 0.2) +
  labs(title = "Predicted Values", x = "Year", y = "Value") +
  theme_light()


ggsave(paste(path, '/predicted_values.png', sep=''), width = 8)

}

##########################################Industry Predicted Figs

volumes$bin <- factor(volumes$bin)

# model_formula_industry <- as.formula(paste0(
#   'progress_main_percentile', " ~ ",
#   category_religion, "*",
#   category_science, "*industry_percentile*bin + ",
#   category_religion, "*",
#   category_flexible, "*industry_percentile*bin + ",
#   category_science, "*",
#   category_flexible, "*industry_percentile*bin - ",
#   category_religion, "*industry_percentile*bin + ",
#   "bin*industry_percentile + Year"
# ))

model_formula_industry <- as.formula(paste0(
  'progress_main_percentile', " ~ ",
  category_religion, "*",
  category_science, "*industry_percentile*bin + ",
  category_religion, "*",
  category_flexible, "*industry_percentile*bin + ",
  category_science, "*",
  category_flexible, "*industry_percentile*bin - ",
  category_religion, "*industry_percentile*bin + ",
  "bin*industry_percentile"
))


model_marginal_predicted_industry <- lm(model_formula_industry, data = volumes)
print(summary(model_marginal_predicted_industry))

pred_industry <- function(lm, sci, rel, flex, ind){
  cluster = vcovCL(lm, cluster = ~Year)

  data_list <- list()
  data_list[[category_science]] <- sci
  data_list[[category_religion]] <- rel
  data_list[[category_flexible]] <- flex
  data_list[["industry_percentile"]] <- ind
  data_list[["bin"]] <- bins
  # data_list[["Year"]] <- bins_numeric

  data <- as.data.frame(data_list)
  # return(data)
  prediction <- Predict(lm, newdata = data, interval = "confidence", se.fit =TRUE, vcov = cluster)
  fit <- data.frame(prediction$fit)
  return(fit)
}



s100_0 <- pred_industry(lm = model_marginal_predicted_industry, sci = 1, rel = 0, flex = 0, ind = 0)
s50r50_0 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0.5, rel = 0.5, flex = 0, ind = 0)
s50f50_0 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0.5, rel = 0, flex = 0.5, ind = 0)
thirds_0 <- pred_industry(lm = model_marginal_predicted_industry, sci = 1/3, rel = 1/3, flex = 1/3, ind = 0)
r50f50_0 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0, rel = 0.5, flex = 0.5, ind = 0)


s100_1 <- pred_industry(lm = model_marginal_predicted_industry, sci = 1, rel = 0, flex = 0, ind = 0.9)
s50r50_1 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0.5, rel = 0.5, flex = 0, ind = 0.9)
s50f50_1 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0.5, rel = 0, flex = 0.5, ind = 0.9)
thirds_1 <- pred_industry(lm = model_marginal_predicted_industry, sci = 1/3, rel = 1/3, flex = 1/3, ind = 0.9)
r50f50_1 <- pred_industry(lm = model_marginal_predicted_industry, sci = 0, rel = 0.5, flex = 0.5, ind = 0.9)

s100_p$label <- paste0("100% ", category_science)
s50r50_p$label <- paste0("50% ", category_science, " 50% ", category_religion)
s50f50_p$label <- paste0("50% ", category_science, " 50% ", category_flexible)
thirds_p$label <- "1/3 Each"
r50f50_p$label <- paste0("50% ", category_religion, " 50% ", category_flexible)

s100_0$label <- paste0("100% ", category_science)
s50r50_0$label <- paste0("50% ", category_science, " 50% ", category_religion)
s50f50_0$label <- paste0("50% ", category_science, " 50% ", category_flexible)
thirds_0$label <- "1/3 Each"
r50f50_0$label <- paste0("50% ", category_religion, " 50% ", category_flexible)

s100_1$label <- paste0("100% ", category_science)
s50r50_1$label <- paste0("50% ", category_science, " 50% ", category_religion)
s50f50_1$label <- paste0("50% ", category_science, " 50% ", category_flexible)
thirds_1$label <- "1/3 Each"
r50f50_1$label <- paste0("50% ", category_religion, " 50% ", category_flexible)


s100_0$bin <- bins
s50r50_0$bin <- bins
s50f50_0$bin <- bins
thirds_0$bin <- bins
r50f50_0$bin <- bins

s100_1$bin <- bins
s50r50_1$bin <- bins
s50f50_1$bin <- bins
thirds_1$bin <- bins
r50f50_1$bin <- bins

predicted_0 <- rbind(s100_0, s50r50_0, s50f50_0, thirds_0, r50f50_0)

predicted_1 <- rbind(s100_1, s50r50_1, s50f50_1, thirds_1, r50f50_1)

predicted_0$bin <- as.numeric(as.character(predicted_0$bin))
predicted_1$bin <- as.numeric(as.character(predicted_1$bin))

predicted_fig_0 <- ggplot(predicted_0, aes(x = bin, y = fit, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(y = fit, ymin = lwr, ymax = upr, fill = label), alpha = 0.2) +
  labs(title = "Predicted Values (Ind = 0)", x = "Year", y = "Value") +
  # scale_y_continuous(oob=rescale_none) +
  # ylim(-2.5, 5)+
  coord_cartesian(ylim = c(-2.5,5)) +
  theme_light() +
  theme(legend.position = "none")

show(predicted_fig_0)


predicted_fig_1 <- ggplot(predicted_1, aes(x = bin, y = fit, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(y = fit, ymin = lwr, ymax = upr, fill = label), alpha = 0.2) +
  labs(title = "Predicted Values (Ind = 90th Percentile)", x = "Year", y = "Value") +
  # scale_y_continuous(limits = c(-1,1), oob = rescale_none) +
  # ylim(-2.5,5)+
  coord_cartesian(ylim = c(-2.5,5)) +
  theme_light()

show(predicted_fig_1)

figure <- ggarrange(predicted_fig_0, predicted_fig_1,
                    labels = c("A", "B"),
                    ncol = 2, nrow =1,
                    widths = c(5.5,8))
show(figure)

path <- paste(output_folder, 'regression_figures/industry_percentile', sep='')

if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)
  
  print('directory created')
}else{
  print("dir exists")
}

ggsave(paste(path, '/predicted_values.png', sep =''), width = 13.5)

######################################Figure with different values of industry

# Set science = 0.5, flexible = 0.5, religion = 0
industry_levels <- c(0, 0.25, 0.5, 0.75, 1)
pred_list <- list()

for (ind in industry_levels) {
  pred_df <- pred_industry(
    lm = model_marginal_predicted_industry,
    sci = 0.5,
    rel = 0,
    flex = 0.5,
    ind = ind
  )
  pred_df$bin <- bins
  pred_df$industry_percentile <- ind
  pred_df$label <- paste0("Industry = ", ind)
  pred_list[[as.character(ind)]] <- pred_df
}

#add progress regression line
s50f50_p$label <- "Progress Regression (No Industry)"
s50f50_p$industry_percentile <- NA  # Not used, but for consistent structure

pred_list[['progress_reg']] <- s50f50_p


# Combine all predictions into one dataframe
pred_combined <- bind_rows(pred_list)

# Convert bin to numeric (if needed)
pred_combined$bin <- as.numeric(as.character(pred_combined$bin))


predicted_fig <- ggplot(pred_combined, aes(x = bin, y = fit, group = label)) +
  geom_line(aes(color = label, linetype = label)) +
  geom_ribbon(aes(ymin = lwr, ymax = upr, fill = label), alpha = 0.2) +
  labs(
    x = "Year",
    y = "Predicted Value"
  ) +
  theme_light() +
  theme(axis.text = element_text(size=10),
        legend.text = element_text(size=12),
        legend.title = element_text(size = 12),
        axis.title = element_text(size = 12))

# Show plot
print(predicted_fig)

ggsave(paste(path, '/predicted_values_sci_pe.png', sep =''), width = 13.5)
