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
library(modelsummary)

#load configuration file
config <- yaml.load_file('./Rscripts/r_config.yaml')

volumes <- read.csv(paste(config$temporary_path, 'volumes_scores.csv', sep = '/'))

output_folder <- config$output_path

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

#change empty author values to NAs
volumes$authors <- ifelse(volumes$authors == '', NA, volumes$authors)

#Drop obs before 1600

volumes <- volumes %>%
  filter(Year > min_year)

#Regressions
reference = min(bins)

print(names(volumes))

progress_var <- 'progress_main_percentile'

# #Uses feols to carry clustered SEs throughout
# mod <- feols(.[progress_var] ~ Science
#              + Political.Economy
#              + Science*Political.Economy
#              + Science*Religion
#              + Religion*Political.Economy
#              + i(bin, Science, reference)
#              + i(bin, Political.Economy, reference)
#              + i(bin, Science*Religion, reference)
#              + i(bin, Science*Political.Economy, reference)
#              + i(bin, Political.Economy*Religion, reference)
#              + i(bin, ref = reference)
#              - Religion
#              + Year, data = volumes, cluster = c("Year"))
if (config$author_fe == TRUE) {
  mod <- feols(.[progress_var] ~ Science
             + Political.Economy
             + Science*Political.Economy
             + Science*Religion
             + Religion*Political.Economy
             + i(bin, Science, reference)
             + i(bin, Political.Economy, reference)
             + i(bin, Science*Religion, reference)
             + i(bin, Science*Political.Economy, reference)
             + i(bin, Political.Economy*Religion, reference)
             + i(bin, ref = reference)
             - Religion | authors, data = volumes, cluster = c("Year"))
} else {
#Uses feols to carry clustered SEs throughout
mod <- feols(.[progress_var] ~ Science
             + Political.Economy
             + Science*Political.Economy
             + Science*Religion
             + Religion*Political.Economy
             + i(bin, Science, reference)
             + i(bin, Political.Economy, reference)
             + i(bin, Science*Religion, reference)
             + i(bin, Science*Political.Economy, reference)
             + i(bin, Political.Economy*Religion, reference)
             + i(bin, ref = reference)
             - Religion , data = volumes, cluster = c("Year"))

}

print(summary(mod))

estimates <- tibble::rownames_to_column(as.data.frame(mod$coeftable), "coefficient")

#parse variable names into FEs and dep vars


estimates <- estimates %>%
  mutate(coefficient = str_remove(coefficient, "bin::")) %>%
  mutate(coefficient = str_replace(coefficient, '^([^0-9:]*):([^0-9:]*)$', '\\1 * \\2')) %>% #Format interactions correctly
  mutate(split = strsplit(coefficient, ':')) %>%
  mutate(year = sapply(split, function(x) x[1]),
         variable = ifelse(sapply(split, length) == 2, sapply(split, function(x) x[2]), sapply(split, function(x) x[1]))) %>% #assign years and variables to correct columns
  select(-split)

estimates <- estimates %>%
  mutate(variable = ifelse(is.na(as.numeric(variable)), variable, "(Intercept)")) %>%
  mutate(year = ifelse(is.na(as.numeric(year)), 'Reference', year))

#Reshape coefficients and std errors into dfs

transform_estimates <- function(df, stat){
  transformed <- dcast(df, variable ~ year, value.var = stat)
  
  transformed <- transformed %>%
    relocate("Reference", .after = "variable") %>%
    arrange(str_length(variable), variable) %>%
    arrange(variable != "(Intercept)")
  
  return(transformed)
}

coefs <- transform_estimates(estimates, "Estimate")
std_errs <- transform_estimates(estimates, "Std. Error")
pvalue <- transform_estimates(estimates, "Pr(>|t|)")



#Get output into models to be compatible with modelsummary
models <- list()

for (i in 2:ncol(coefs)){
  
  model <- list()
  
  class(model) <- "custom"
  
  tidy.custom <- function(x, ...) {
    data.frame(
      term = coefs$variable,
      estimate = coefs[[i]],
      std.error = std_errs[[i]],
      p.value = pvalue[[i]]
    )
  }
  
  #10 because that is the first model in the second of the split results table. Need to change to 2 if going for one continuous table
  if (i == 2) {
    
    glance.custom <- function(x, ...) {
      data.frame(
        "nobs" = mod$nobs,
        "r.squared" = glance(mod)$r.squared
        # "adj.r.squared" = glance(mod)$adj.r.squared
      )
    }
  } else{
    glance.custom <- function(x, ...) {
      data.frame(
      )
    }
  }
  models[[colnames(coefs)[[i]]]] <- modelsummary(model, output = "modelsummary_list")
}

#r Main results table
rename <- c("Political.Economy" = "PolitEcon", "industry_percentile" = "Industry",
            "Science * Religion" = "$\\text{Science} \\times \\text{Religion}$",
            "Science:industry_percentile" = "$\\text{Science} \\times \\text{Industry}$",
            "Religion:industry_percentile" = "$\\text{Religion} \\times \\text{Industry}$",
            "Science * Political.Economy" = "$\\text{Science} \\times \\text{PolitEcon}$",
            "Political.Economy * Religion" = "$\\text{Religion} \\times \\text{PolitEcon}$",
            "Science:Religion:industry_percentile" = "$\\text{Science} \\times \\text{Religion} \\times \\text{Industry}$",
            "Science:industry_percentile:Political.Economy" = "$\\text{Science} \\times \\text{PolitEcon} \\times \\text{Industry}$",
            "Religion:industry_percentile:Political.Economy" = "$\\text{Religion} \\times \\text{PolitEcon} \\times \\text{Industry}$")

note <- "Volumes are placed into 50 year ((+/-) 25 year) bins. Columns represent interactions between bin fixed effects and the variables of interest (rows). Observations prior to 1600 are dropped. Standard errors are clustered by year of publication."

coef_omitted <- "Year"


modelsummary(models, stars = TRUE)

reg_path <- paste(output_folder, 'regression_tables/', progress_var, sep = '')


if (!dir.exists(reg_path)){
  dir.create(reg_path, recursive = TRUE)
  
  print('directory created')
}else{
  print("dir exists")
}

if (config$author_fe == TRUE) {
  modelsummary(models,
               stars = TRUE,
               coef_rename = rename,
               coef_omit = coef_omitted,
               title = "Dependent Variable: Progress Percentile",
               escape = FALSE,
               threeparttable = TRUE,
               notes = note,
               output=paste(reg_path, '/results_author_fe.tex', sep = '')
  )
} else {
modelsummary(models,
             stars = TRUE,
             coef_rename = rename,
             coef_omit = coef_omitted,
             title = "Dependent Variable: Progress Percentile",
             escape = FALSE,
             threeparttable = TRUE,
             notes = note,
             output=paste(reg_path, '/results.tex', sep = '')
)

}
##########################################Industry Regressions##########################################


industry_vars <- list('industry_percentile')


for (ind in industry_vars){
  
volumes$industry_percentile <- volumes[[ind]]

#iterate through industry score versions
# 
# mod <- feols(progress_main_percentile ~ Science +
#                Political.Economy +
#                industry_percentile +
#                Science*Political.Economy +
#                Science*Religion +
#                Religion*Political.Economy +
#                Science*industry_percentile +
#                Political.Economy*industry_percentile +
#                # Religion*industry_percentile +
#                Science*Political.Economy*industry_percentile +
#                Science*Religion*industry_percentile +
#                Religion*Political.Economy*industry_percentile +
#                i(bin, Science, reference) +
#                i(bin, Political.Economy, reference) +
#                i(bin, industry_percentile, reference) +
#                i(bin, Science*Religion, reference) +
#                i(bin, Science*Political.Economy, reference) +
#                i(bin, Political.Economy*Religion, reference) +
#                i(bin, Science*industry_percentile, reference) +
#                i(bin, Political.Economy*industry_percentile, reference) +
#                # i(bin, Religion*industry_percentile, 1610) +
#                i(bin, Science*Political.Economy*industry_percentile, reference) +
#                i(bin, Science*Religion*industry_percentile, reference) +
#                i(bin, Religion*Political.Economy*industry_percentile, reference) +
#                i(bin, ref = reference) -
#                Religion -
#                Religion*industry_percentile+
#                industry_percentile +
#                Year,
#              data = volumes, cluster = c("Year"))
if (config$author_fe == TRUE) {
mod <- feols(progress_main_percentile ~ Science +
               Political.Economy +
               industry_percentile +
               Science*Political.Economy +
               Science*Religion +
               Religion*Political.Economy +
               Science*industry_percentile +
               Political.Economy*industry_percentile +
               # Religion*industry_percentile +
               Science*Political.Economy*industry_percentile +
               Science*Religion*industry_percentile +
               Religion*Political.Economy*industry_percentile +
               i(bin, Science, reference) +
               i(bin, Political.Economy, reference) +
               i(bin, industry_percentile, reference) +
               i(bin, Science*Religion, reference) +
               i(bin, Science*Political.Economy, reference) +
               i(bin, Political.Economy*Religion, reference) +
               i(bin, Science*industry_percentile, reference) +
               i(bin, Political.Economy*industry_percentile, reference) +
               # i(bin, Religion*industry_percentile, 1610) +
               i(bin, Science*Political.Economy*industry_percentile, reference) +
               i(bin, Science*Religion*industry_percentile, reference) +
               i(bin, Religion*Political.Economy*industry_percentile, reference) +
               i(bin, ref = reference) -
               Religion -
               Religion*industry_percentile+
               industry_percentile | authors,
             data = volumes, cluster = c("Year"))
} else {
mod <- feols(progress_main_percentile ~ Science +
               Political.Economy +
               industry_percentile +
               Science*Political.Economy +
               Science*Religion +
               Religion*Political.Economy +
               Science*industry_percentile +
               Political.Economy*industry_percentile +
               # Religion*industry_percentile +
               Science*Political.Economy*industry_percentile +
               Science*Religion*industry_percentile +
               Religion*Political.Economy*industry_percentile +
               i(bin, Science, reference) +
               i(bin, Political.Economy, reference) +
               i(bin, industry_percentile, reference) +
               i(bin, Science*Religion, reference) +
               i(bin, Science*Political.Economy, reference) +
               i(bin, Political.Economy*Religion, reference) +
               i(bin, Science*industry_percentile, reference) +
               i(bin, Political.Economy*industry_percentile, reference) +
               # i(bin, Religion*industry_percentile, 1610) +
               i(bin, Science*Political.Economy*industry_percentile, reference) +
               i(bin, Science*Religion*industry_percentile, reference) +
               i(bin, Religion*Political.Economy*industry_percentile, reference) +
               i(bin, ref = reference) -
               Religion -
               Religion*industry_percentile+
               industry_percentile,
             data = volumes, cluster = c("Year"))

}
print(summary(mod))

estimates <- tibble::rownames_to_column(as.data.frame(mod$coeftable), "coefficient")

#parse variable names into FEs and dep vars
estimates <- estimates %>%
  mutate(coefficient = str_remove(coefficient, "bin::")) %>%
  mutate(coefficient = str_replace(coefficient, '^([^0-9:]*):([^0-9:]*)$', '\\1 * \\2')) %>% #Format interactions correctly
  mutate(coefficient = str_replace(coefficient, '^([^0-9:]*):([^0-9:]*):([^0-9:]*)$', '\\1 * \\2 * \\3')) %>%
  mutate(split = strsplit(coefficient, ':')) %>%
  mutate(year = sapply(split, function(x) x[1]),
         variable = ifelse(sapply(split, length) == 2, sapply(split, function(x) x[2]), sapply(split, function(x) x[1]))) %>% #assign years and variables to correct columns
  select(-split)

#Fix some special cases
estimates <- estimates %>%
  mutate(variable = ifelse(is.na(as.numeric(variable)), variable, "(Intercept)")) %>%
  mutate(year = ifelse(is.na(as.numeric(year)), 'Reference', year)) %>%
  mutate(variable = ifelse(variable == 'Political.Economy * industry_percentile * Religion', 'Religion * Political.Economy * industry_percentile', variable)) %>%
  mutate(variable = ifelse(variable == 'Science * industry_percentile * Religion', 'Science * Religion * industry_percentile', variable))


#Reshape coefficients, std. errors, and pvalues into dfs

transform_estimates <- function(df, stat){
  transformed <- dcast(df, variable ~ year, value.var = stat)
  
  transformed <- transformed %>%
    relocate("Reference", .after = "variable") %>%
    arrange(str_length(variable), variable) %>%
    arrange(variable != "(Intercept)" & variable != "industry_percentile")
  
  return(transformed)
}
coefs <- transform_estimates(estimates, "Estimate")
std_errs <- transform_estimates(estimates, "Std. Error")
pvalue <- transform_estimates(estimates, "Pr(>|t|)")

models <- list()

for (i in 2:ncol(coefs)){
  print(ncol(coefs))
  model <- list()
  class(model) <- "custom"
  tidy.custom <- function(x, ...) {
    data.frame(
      term = coefs$variable,
      estimate = coefs[[i]],
      std.error = std_errs[[i]],
      p.value = pvalue[[i]]
    )
  }
  
  #10 because that is the first model in the second half of results. No way to generalize, is what it is given how we are presenting results. Change to 2 for a generalized results table.
  if (i == 2) {
    glance.custom <- function(x, ...) {
      data.frame(
        "nobs" = mod$nobs,
        "r.squared" = glance(mod)$r.squared
        # "adj.r.squared" = glance(mod)$adj.r.squared
      )
    }
  } else{
    glance.custom <- function(x, ...) {
      data.frame(
      )
    }
  }
  models[[colnames(coefs)[[i]]]] <- modelsummary(model, output = "modelsummary_list")
}

#Modelsummary table

cm <- c("Political.Economy" = "PolitEcon",
        "industry_percentile" = "Industry",
        "Science * Religion" = "$\\text{Science} \\times \\text{Religion}$",
        "Science * industry_percentile" = "$\\text{Science} \\times \\text{Industry}$",
        "Religion:industry_percentile" = "$\\text{Religion} \\times \\text{Industry}$",
        "Science * Political.Economy" = "$\\text{Science} \\times \\text{PolitEcon}$",
        "Political.Economy * Religion" = "$\\text{Religion} \\times \\text{PolitEcon}$",
        "Science:Religion:industry_percentile" = "$\\text{Science} \\times \\text{Religion} \\times \\text{Industry}$",
        "Science:industry_percentile:Political.Economy" = "$\\text{Science} \\times \\text{PolitEcon} \\times \\text{Industry}$",
        "Religion:industry_percentile:Political.Economy" = "$\\text{Religion} \\times \\text{PolitEcon} \\times \\text{Industry}$",
        "Political.Economy * industry_percentile" = "$\\text{PolitEcon} \\times \\text{Industry}$",
        "Science * Religion * industry_percentile" = "$\\text{Science} \\times \\text{Religion} \\times \\text{Industry}$",
        "Science * Political.Economy * industry_percentile" = "$\\text{Science} \\times \\text{PolitEcon} \\times \\text{Industry}$",
        "Religion * Political.Economy * industry_percentile" = "$\\text{Religion} \\times \\text{PolitEcon} \\times \\text{Industry}$")


coef_omitted <- "Year"

note <- "Volumes are placed into 50 year ((+/-) 25 year) bins. Columns represent interactions between bin fixed effects and the variables of interest (rows). Observations prior to 1600 are dropped. $Industry$ represents the industry score by percentile over the whole corpus. Standard errors are clustered by year of publication."


modelsummary(models,
             coef_omit = "Year",
             stars = TRUE)

reg_path <- paste(output_folder, 'regression_tables/', ind, sep = '')


if (!dir.exists(reg_path)){
  dir.create(reg_path, recursive = TRUE)
  
  print('directory created')
}else{
  print("dir exists")
}

if (config$author_fe == TRUE) {
  modelsummary(models,
               stars = TRUE,
               coef_rename = cm,
               coef_omit = coef_omitted,
               title = 'Dependent Variable: Progress Percentile',
               escape = FALSE,
               threeparttable = TRUE,
               notes = note,
               output=paste(reg_path, '/results_author_fe.tex', sep = ''))
} else {
modelsummary(models,
             stars = TRUE,
             coef_rename = cm,
             coef_omit = coef_omitted,
             title = 'Dependent Variable: Progress Percentile',
             escape = FALSE,
             threeparttable = TRUE,
             notes = note,
             output=paste(reg_path, '/results.tex', sep = ''))

}
}