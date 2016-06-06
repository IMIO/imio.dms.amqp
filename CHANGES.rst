Changelog
=========

0.1.11 (unreleased)
-------------------

- Nothing changed yet.


0.1.10 (2016-06-06)
-------------------

- Reindex incomingmail SearchableText index containing scan_id.
  [sgeulette]

0.1.9 (2016-04-22)
------------------

- Handle properly multiple versions for files
  [mpeeters]


0.1.8 (2016-04-15)
------------------

- When consuming, retry 10 times in case of zodb conflict error.
  [mpeeters]

0.1.7 (2015-12-11)
------------------

- Initialize to empty list recipient_groups to avoid diff error.
  [sgeulette]

0.1.6 (2014-12-04)
------------------

- Set reception_date as scan_date when creating incomingdmsmail.
  [sgeulette]


0.1.5 (2014-11-28)
------------------

- filter metadata to separate dmsmail and mainfile attributes
  [sgeulette]
- Get file by the scan_id index
  [sgeulette]


0.1.4 (2014-11-27)
------------------

- Set scan fields on main file.
  [sgeulette]


0.1.3 (2014-10-24)
------------------

- Correct bug when updating file. Id must not be changed (in unicode)
  [sgeulette]


0.1.2 (2014-10-23)
------------------

- Correct bug when deleting file to replace.
  [sgeulette]
- Remove ownership change when updating.
  [sgeulette]


0.1.1 (2014-10-17)
------------------

- Remove external_reference_no set
  [sgeulette]


0.1 (2014-10-17)
----------------

- Initial release
  [mpeeters]
