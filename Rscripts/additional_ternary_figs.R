rm(list=ls())
options(scipen=999)

library(ggtern)
library(tidyverse)
library(biscale)
library(cowplot)
library(yaml)

setwd('E:/grad_school/research/AIKR/')

config <- yaml.load_file('./Rscripts/r_config.yaml')

volumes <- read.csv(paste(config$temporary_path, 'volumes_scores.csv', sep = '/'))

output_folder <- config$output_path

if (config$half_century == TRUE){
  years <- seq(1550, 1850, by = 50)
}else{
  years <- seq(1510, 1890, by = 1)
}

#########################SUBTRIANGLES

#Find max and min scores for optimism and volume count out of subtriangles, for use in scaling legends
percentiles <- c()
vol_count <- c()

for (year in years){
  df <- volumes %>% filter(Year >= year - 10,
                           Year <= year + 10)
  
  tmp_fig <- ggtern(df, aes(x = Political.Economy, y = Religion, z = Science)) + 
    geom_tri_tern(bins=5, aes(fill = ..stat.., value = progress_main_percentile), fun = mean) +
    stat_tri_tern(bins = 5, geom = 'point',
                  aes(size = ..count.., value = progress_main_percentile),
                  color="white",
                  centroid = TRUE) +
    labs(x = 'Political Economy', y = 'Religion', z = 'Science', title = year, fill = 'Progress (Percentile)', size = 'Volumes')
  dat <- layer_data(tmp_fig, 1)
  
  percentiles <- append(percentiles, dat$stat) #append percentiles of subtriangles to list
  vol_count <- append(vol_count, dat$count) #append volume counts of subtriangles to list
  
  
  
}

percentiles <- na.omit(percentiles)
vol_count <- na.omit(vol_count)
#Generate figures for paper

figure_list <- list()
label = seq(0,1,by=0.2)

#create filepath
path <- paste(output_folder, 'subtriangles', sep = '')
if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)
  
  print('directory created')
}else{
  print('dir exists')
}

for (year in years){
  df <- volumes %>% filter(Year >= year - 10,
                           Year <= year + 10)
  
  plot <- ggtern(df, aes(x = Political.Economy, y = Religion, z = Science)) +
    geom_tri_tern(bins=5, aes(fill=..stat.., value = progress_main_percentile), fun = mean) +
    stat_tri_tern(bins = 5, geom='point',
                  aes(size=..count.., progress_main_percentile),
                  color='white', centroid = TRUE) +
    labs(x = 'Political\nEconomy', y = "Religion", z = "Science", title = year, fill = 'Progress (Percentile)', size = "Volumes") +
    
    #  scale_fill_gradient(low="blue", high="red", na.value="white") +    #Uncomment for red/blue theme
    # scale_fill_gradient(low="blue", high="red", na.value="white", limits = c(0,1)) + #Uncomment for red/blue theme with full gradient scale
    # scale_fill_gradient(low="#56B1F7",high="#132B43", na.value="white",limits=c(0,1))+ #Uncomment for blue theme with full percentile gradient scale
    # scale_fill_gradient(low = "#56B1F7",high="#132B43", na.value="white")+#Uncomment for blue theme    
    
    
    scale_fill_gradient(low = "#56c7f7",high="#132B43", na.value="white",
                        limits = c(0, 1),
                        breaks = c(0,0.25, 0.5, 0.75, 1))+#Lighter blue
    
    scale_size_continuous(range = c(0,10),
                          limits = c(1, 8000),
                          breaks = c(10, 100, 1000, 2500, 5000, 8000)) + #Set limits and breaks of volume dots
    
    limit_tern(limits=c(0,1.0),
               breaks=seq(0,1,by=0.2),
               labels=label)+
    
    guides(size=guide_legend(reverse=TRUE, order = 0),
           fill = guide_colorbar(title = 'Percentile',
                                 limits = c(0,1),
                                 breaks = seq(0,1,by=0.25)))+
    theme_dark()+
    {if(year != 1850)theme(legend.position = "none")}+
    theme(tern.axis.title.R = element_text(hjust=0.6, vjust = 0.9), tern.axis.title.L = element_text(hjust = 0.3, vjust = 0.9))
  
  # tmp <- ggplotGrob(plot)
  
  # figure_list[[toString(year)]] <- plot
  
  ggsave(paste(path, '/', year, '.png', sep = ''),width = 6.5, height = 4.5)
}




###############################################BISCALE TRIANGLES#############################

bi_palette <- 'DkViolet2'
dimensions <- 4

#create filepath
path <- paste(output_folder, 'biscale_triangles', sep = '')
if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)
  
  print('directory created')
}else{
  print('dir exists')
}

#make industry column name consistent
if ("industry_1643_percentile" %in% names(df)) {
  names(df)[names(df) == "industry_1643_percentile"] <- "industry_percentile"
}

volumes <- bi_class(volumes, x = progress_main_percentile, y = industry_percentile, style = 'equal', dim = dimensions)

for (year in years){
  
  if (config$bins == TRUE){
    df <- volumes %>% filter(Year >= year - 10,
                             Year <= year + 10)
  }else{
    df <- volumes %>% filter(Year == year)
  }
  
  fig <- ggtern(data = df, mapping = aes(x = Political.Economy, y = Religion, z = Science ,color = bi_class)) +
    geom_point(show.legend = FALSE) +
    bi_scale_color(pal = bi_palette, dim = 4) +
    labs(x = 'Political\nEconomy', y = 'Religion', z = 'Science', title = year) +
    limit_tern(limits=c(0,1.0),
               breaks=seq(0,1,by=0.2),
               labels=seq(0,1,by=0.2))+
    theme_classic() +
    theme(tern.axis.title.R = element_text(hjust=0.6, vjust = 0.9, size = 18),
          tern.axis.title.L = element_text(hjust = 0.3, vjust = 0.9, size = 18),
          tern.axis.title.T = element_text(size = 18),
          title = element_text(size = 18),
          axis.text = element_text(size = 15),
          plot.margin = margin(0,0,-15,0))
  
  if(year == 1850){
    legend <- bi_legend(pal = bi_palette,
                        dim = dimensions,
                        xlab = "Higher Progress",
                        ylab = "Higher Industry",
                        size = 18)
    
    fig_go <- ggplotGrob(fig)
    
    fig_combined <- ggdraw() +
      draw_plot(fig_go, 0, 0, 1, 1) +
      draw_plot(legend, 0.62, 0.4, 0.5, 0.5)
    show(fig_combined)
    ggsave(paste(path, '/', year, '.png', sep = ''), plot = fig_combined, width = 12, height = 6.5)
    
  }else{
    show(fig)
    ggsave(paste(path, '/', year, '.png', sep = ''), plot = fig, width = 8, height = 6.5)
  }
}


###########Biscale triangles using alternative industry

bi_palette <- 'DkViolet2'
dimensions <- 4

#create filepath
path <- paste(output_folder, 'biscale_triangles_industry_1708', sep = '')
if (!dir.exists(path)){
  dir.create(path, recursive = TRUE)
  
  print('directory created')
}else{
  print('dir exists')
}

#make industry column name consistent
if ("industry_1643_percentile" %in% names(df)) {
  names(df)[names(df) == "industry_1643_percentile"] <- "industry_percentile"
}

volumes <- bi_class(volumes, x = progress_main_percentile, y = industry_1708_percentile, style = 'equal', dim = dimensions)

for (year in years){
  
  if (config$bins == TRUE){
    df <- volumes %>% filter(Year >= year - 10,
                             Year <= year + 10)
  }else{
    df <- volumes %>% filter(Year == year)
  }
  
  fig <- ggtern(data = df, mapping = aes(x = Political.Economy, y = Religion, z = Science ,color = bi_class)) +
    geom_point(show.legend = FALSE) +
    bi_scale_color(pal = bi_palette, dim = 4) +
    labs(x = 'Political\nEconomy', y = 'Religion', z = 'Science', title = year) +
    limit_tern(limits=c(0,1.0),
               breaks=seq(0,1,by=0.2),
               labels=seq(0,1,by=0.2))+
    theme_classic() +
    theme(tern.axis.title.R = element_text(hjust=0.6, vjust = 0.9, size = 18),
          tern.axis.title.L = element_text(hjust = 0.3, vjust = 0.9, size = 18),
          tern.axis.title.T = element_text(size = 18),
          title = element_text(size = 18),
          axis.text = element_text(size = 15),
          plot.margin = margin(0,0,-15,0))
  
  if(year == 1850){
    legend <- bi_legend(pal = bi_palette,
                        dim = dimensions,
                        xlab = "Higher Progress",
                        ylab = "Higher Industry",
                        size = 18)
    
    fig_go <- ggplotGrob(fig)
    
    fig_combined <- ggdraw() +
      draw_plot(fig_go, 0, 0, 1, 1) +
      draw_plot(legend, 0.62, 0.4, 0.5, 0.5)
    show(fig_combined)
    ggsave(paste(path, '/', year, '.png', sep = ''), plot = fig_combined, width = 12, height = 6.5)
    
  }else{
    show(fig)
    ggsave(paste(path, '/', year, '.png', sep = ''), plot = fig, width = 8, height = 6.5)
  }
}











