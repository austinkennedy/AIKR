rm(list=ls())
options(scipen=999)

library(ggtern)
library(tidyverse)
library(yaml)

config <- yaml.load_file('./Rscripts/r_config.yaml')

volumes <- read.csv(paste(config$temporary_path, 'volumes_scores.csv', sep = '/'))
famous_books <- read.csv(paste(config$input_path, 'famous_books.csv', sep = '/'))

famous_merged <- merge(volumes[,c('HTID', 'Religion', 'Science', 'Political.Economy')], famous_books, by = 'HTID')

write.csv(famous_merged, paste(config$temporary_path, 'famous_merged.csv', sep = '/'))

#set seed for reproducability
set.seed(42)

famous_selected <- famous_merged %>%
  group_by(Title) %>%
  slice_sample(n=1)
# 
# famous_selected <- famous_selected %>%
#   group_by(Category) %>%
#   mutate(shape = row_number())

famous_selected <- famous_selected %>%
  group_by(Category) %>%
  arrange(Category, Year) %>%
  mutate(shape = row_number()) %>%
  ungroup()

color_map <- data.frame(Category = c('Religion', 'Political Economy', 'Science', 'Literature'),
                        color = c('blue', 'red', 'green4', 'darkorchid'))

color_map_gray <- data.frame(Category = c('Religion', 'Political Economy', 'Science', 'Literature'),
                        color_gray = c(rgb(100,100,100, maxColorValue = 255), rgb(160,160,160, maxColorValue = 255), rgb(0,0,0, maxColorValue = 255), rgb(220,220,220, maxColorValue = 255)))

famous_selected <- famous_selected %>% left_join(color_map, by = 'Category')
famous_selected <- famous_selected %>% left_join(color_map_gray, by = 'Category')

label = seq(0,1,by=0.2)



plot <- ggtern(famous_selected, aes(x = Political.Economy, y = Religion, z = Science, shape = Title, color = Title)) +
  geom_point(size = 2, stroke = 1.2) +
  scale_shape_manual(values = famous_selected$shape, labels = famous_selected$Title, breaks = famous_selected$Title) +
  scale_color_manual(values = famous_selected$color, labels = famous_selected$Title, breaks = famous_selected$Title) +

  limit_tern(limits=c(0,1.0),
             breaks=seq(0,1,by=0.2),
             labels=label) +
  labs(x = 'Political\nEconomy', y = 'Religion', z = 'Science')+
  theme_classic() +
  theme(tern.axis.title.R = element_text(hjust=0.6, vjust = 0.9, size = 10), tern.axis.title.L = element_text(hjust = 0.3, vjust = 0.9, size = 10),
        tern.axis.title.T = element_text(size = 10),
        legend.title = element_text(size = 10, face = 'bold'), legend.text = element_text(size = 10), legend.spacing.y = unit(0.1, 'cm')) +
  guides(color = guide_legend(byrow =TRUE, size =7),
         shape = guide_legend(byrow=TRUE, size =7))
  
  

path <- paste(config$output_path, 'famous_volumes.png', sep = '/')

ggsave(path, plot, width = 9)

#####grayscale

plot_gray <- ggtern(famous_selected, aes(x = Political.Economy, y = Religion, z = Science, shape = Title, color = Title)) +
  geom_point(size = 2, stroke = 1.2) +
  scale_shape_manual(values = famous_selected$shape, labels = famous_selected$Title, breaks = famous_selected$Title) +
  scale_color_manual(values = famous_selected$color_gray, labels = famous_selected$Title, breaks = famous_selected$Title) +
  
  limit_tern(limits=c(0,1.0),
             breaks=seq(0,1,by=0.2),
             labels=label) +
  labs(x = 'Political\nEconomy', y = 'Religion', z = 'Science')+
  theme_classic() +
  theme(tern.axis.title.R = element_text(hjust=0.6, vjust = 0.9, size = 10), tern.axis.title.L = element_text(hjust = 0.3, vjust = 0.9, size = 10),
        tern.axis.title.T = element_text(size = 10),
        legend.title = element_text(size = 10, face = 'bold'),
        legend.text = element_text(size = 10),
        legend.spacing.y = unit(0.1, 'cm')) +
  guides(color = guide_legend(byrow =TRUE, size =7),
         shape = guide_legend(byrow=TRUE, size =7))


path_gray <- paste(config$output_path, 'famous_volumes_gray.png', sep = '/')

ggsave(path_gray, plot_gray, width = 9)