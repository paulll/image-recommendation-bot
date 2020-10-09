# Catanai bot
Anime picture recommendation bot

## Data
source: `danbooru2019`
preprocessing: `scripts/export_metadata_to_csv`

That is an implicit dataset: we don't have some kind of individual ratings, only likes for each user. 

## Models

- Jaccard index on user likes (collaborative)
- Jaccard index on tags (content-based)
- Logistic regression of the above
- (?) Some kind of SVD / ALS, some matrix magic?

### Jaccard index on user likes

#### Formula
For each user, image pair calculate the following:

```python
# given target_user, image
sum( len(target_user.likes & user.likes) / len(target_user.likes | user.likes) for user in image.likes)
```

Image with the greatest value is the recommended image. 

#### Optimization
The code above is, in practice, slow in large dataset, but we can ignore users with small coefficient, and
that should not significantly lower the quality. 

#### Pros
Simple code, average performance, good quality. 

#### Cons

1. If user belongs to two or more independent clusters (group of users with similar interests), then 
algorithm will recommend only images from the most weighted cluster, ignoring others. So, diversity
suffers.

2. If given image does not belong to our dataset, we can do nothing with it. But it is a disadvantage
for collaborative filtering systems at all.
