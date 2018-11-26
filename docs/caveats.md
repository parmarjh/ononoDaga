## Caveats

- **Unique Ids**: The majority of issues with the data stem from the fact that there is no unique id per row. To fix this, we create a SHA1 hash of all of the text (excluding the timestamp).
	- The primary key (unique identifier) for the `all` and `closed` tables is `{timestamp}_{hash}`. The timestamp for the `pending` table is `{insertion_date}_{hash}`.
	- Keep in mind that the exact same row data (consisting of agency, address, cross streets etc.) can and very likely will happen multiple times so the `hash` by itself is not globally unique. The `timestamp` is not included as part of the `hash` because there is no fixed timestamp for pending events.

- **Immutable Data**: We assume that each row of data is immutable meaning that once it appears on the website it does not change (no change in category, address, etc.). If any data in a row changes, it will be recorded as a new row because the row's `hash` will change. Unfortunately, I don't know how much this assumption actually holds:

	Here is one such case for an item pending dispatch ([May 10 - Pending](https://s3.amazonaws.com/onondaga-e911-prod/index.html#/?type=pending&date=2018-05-10)):

	![](https://i.imgur.com/kHWYCkh.png)

	Here is another case captured in the all (active) page ([May 11 - All](https://s3.amazonaws.com/onondaga-e911-prod/index.html#/?type=all&date=2018-05-11)):

	![](https://i.imgur.com/yjHTXki.png)

	You'll see that the item inserted at 1:08 AM (with hash `6c45a830b5`) is the "actual" item. It has a corresponding row in the "closed" page with the same hash. The other hash (`719a02a814`) is no where to be found ([May 11 - Closed](https://s3.amazonaws.com/onondaga-e911-prod/index.html#/?type=closed&date=2018-05-11)):

	![](https://i.imgur.com/FBuBlNo.png)

	Thus, data changes- it will be difficult to figure out with 100% certainity when this happens. Fortunately, one good clue is that it seems the timestamp remains the same when data changes in the all (active) state.

- **Linking Data**: Data for pending/all/closed events is stored in three separate tables. Looking at a combination of the `hash`, `timestamp`, and the `insertion_timestamp` in each table should help map the lifecycle of an event from pending to all (active) to closed. For example, `(the insertion timestamp of the closed table) - (the insertion timestamp of the `all` table)` should give the length of an event.

- **Pending Events**: The primary key of the pending events table is `{insertion_date}_{hash}`. If an event is inserted near midnight (EST) and remains pending until the next day, a duplicate record will be added. Check the insertion timestamp to ensure there are no back to back records with the same `hash` and consecutive insertion dates.
