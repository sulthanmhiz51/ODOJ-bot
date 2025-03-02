![banner](img\ODOJ-bot_banner.png)

![Static Badge](https://img.shields.io/badge/development_status-under_development-green)

## Table of Contents

## Introduction

### What is ODOJ?
One Day One Juz is a common Quran recitation program. It simply means reading a Juz (Part) of Quran each day, often with a target of completing recitation of the whole Quran (30 Juz) by the end of the month.

ODOJ can be practiced individually, but often practiced as a community so members could remind and support each other.

### ODOJ-bot
ODOJ-bot is a Discord bot designed to help muslim communities managing their One Day One Juz program. With simple Discord commands, communities will gain access to our helpful features, such as role assignment based on Ikhwan or Akhwat, daily and completion (khatam) recitation records, progress tracker, daily reminder, and more.

## Features

### Role Assignment
User can be divided into two roles `Ikhwan` and `Akhwat`. They can choose their role by adding a reaction to a role-message.

![role](img\role0.png)

> Removing the reaction will also remove user's role

If succeed, user will be sent a notification through DM

![role_notif](img\role_notif.png)

### Daily & completion (Khatam) records
When user finishes their recitation, daily or completion, they could simply use the respective command below to record their progress:

 - Daily records [`!khalas`]

![khalas](img\khalas.png)

> Use `!khalas` command for daily record. The bot will prompt verification message before recording your progress

- Completion (Khatam) records [`!khatam`]

![khatam](img\khatam.png)

> Use `!khatam` command for completion record. The bot will prompt verification message before recording your progress

### Progress tracking
User can view their recitation progress by using `!progress` command. Report will be sent through DM

![progress](img\progress.png)

### Daily reminder(under development)
User will be sent daily reminder through DM

![reminder](img\reminder.png)

> We're planning to add personalized reminder toggle command in the future

## Planned features

### - Dashboard
### - ...