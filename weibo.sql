/*
Navicat SQLite Data Transfer

Source Server         : srsv
Source Server Version : 30706
Source Host           : :0

Target Server Type    : SQLite
Target Server Version : 30706
File Encoding         : 65001

Date: 2014-09-04 16:43:45
*/

PRAGMA foreign_keys = OFF;

-- ----------------------------
-- Table structure for "main"."weibo"
-- ----------------------------
DROP TABLE "main"."weibo";
CREATE TABLE "weibo" (
"id"  INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
"nickname"  TEXT NOT NULL,
"title"  TEXT NOT NULL,
"praised"  INTEGER NOT NULL,
"forward"  INTEGER NOT NULL,
"favorite"  INTEGER NOT NULL,
"comment"  INTEGER NOT NULL,
"date"  TEXT NOT NULL,
"time"  TEXT NOT NULL,
"link"  TEXT NOT NULL,
"content"  TEXT NOT NULL,
"datetime"  INTEGER NOT NULL
);

-- ----------------------------
-- Records of weibo
-- ----------------------------
