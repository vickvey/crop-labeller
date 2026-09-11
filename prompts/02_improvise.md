# Adding std dev range in NDVI plot

We need to add std dev range to the plots so that the researchers labelling/correcting labels have an idea of what the wheat range over that region have looked like!! 

I have this:

```bash
```
❯ tree
 .
├──  Gujarat_wheat_2024.csv
├──  Haryana_wheat_2021.csv
├──  Haryana_wheat_2022.csv
├──  Haryana_wheat_2023.csv
├──  Haryana_wheat_2024.csv
├──  Madhya_Pradesh_wheat_2021.csv
├──  Madhya_Pradesh_wheat_2022.csv
├──  Madhya_Pradesh_wheat_2023.csv
├──  Madhya_Pradesh_wheat_2024.csv
├──  Punjab_wheat_2021.csv
├──  Punjab_wheat_2022.csv
├──  Punjab_wheat_2023.csv
├──  Punjab_wheat_2024.csv
├──  Uttar_Pradesh_wheat_2023.csv
└──  Uttar_Pradesh_wheat_2024.csv

~/SUFALAM_DATA/wheat_ndvi                                                                                                                                                         09:41:02 PM
❯ 
```
```


Now, look I want to calculate region wise std dev range of all the states and hardcode save in the repo as it would be good to provide the std dev +-1 range to the researchers working on relabelling/correcting labels in this project.

Btw hey we going to give researchers 15 csv files anyways but not the original complete dataset as shown above, as the above has ~10k datapoints per csv file. I have an algorithm which does outlier analysis and then saves less number of datapoints as compared to ~10k, and that csv file will be given to the researchers to label, so that is what the researchers want for labelling/correcting label.

So basically we want to add average wheat temporal signature +/- 1 standard deviation as reference.
btw we will not supply the original datapoints as shown above to researchers, but provide the hardcoded saved csv's per region haryana, gujarat, madhya pradesh, etc. so that whenever a file belonging to that region is being analyzed the researcher has the average reference.

Now for that you may need to write a script which takes input the original data path that is `~/SUFALAM_DATA/wheat_ndvi/` and produces 5 files corresponding to the data related to reference mean curve and std dev range!!


