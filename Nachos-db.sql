-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: mysql:3306
-- Generation Time: Oct 31, 2024 at 01:10 PM
-- Server version: 9.1.0
-- PHP Version: 8.3.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- Database: `Nachos-db`

-- --------------------------------------------------------
-- Table Structures
-- --------------------------------------------------------

-- Table structure for table `authtoken_token`
CREATE TABLE IF NOT EXISTS `authtoken_token` (
  `key` varchar(40) NOT NULL,
  `created` datetime(6) NOT NULL,
  `user_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_group`
CREATE TABLE IF NOT EXISTS `auth_group` (
  `id` int NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_group_permissions`
CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
  `id` bigint NOT NULL,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_permission`
CREATE TABLE IF NOT EXISTS `auth_permission` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_user`
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` int NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL COLLATE utf8mb4_bin,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `date_of_birth` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_user_groups`
CREATE TABLE IF NOT EXISTS `auth_user_groups` (
  `id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_user_user_permissions`
CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
  `id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `cmgroup`
CREATE TABLE IF NOT EXISTS `cmgroup` (
  `cmgroup_id` int NOT NULL,
  `cmgroup_admin_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `comment`
CREATE TABLE IF NOT EXISTS `comment` (
  `comment_id` int NOT NULL,
  `comment_content` varchar(200) DEFAULT NULL,
  `comment_post_id` int DEFAULT NULL,
  `comment_user_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `django_admin_log`
CREATE TABLE IF NOT EXISTS `django_admin_log` (
  `id` int NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint UNSIGNED NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `django_content_type`
CREATE TABLE IF NOT EXISTS `django_content_type` (
  `id` int NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `django_migrations`
CREATE TABLE IF NOT EXISTS `django_migrations` (
  `id` bigint NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `django_session`
CREATE TABLE IF NOT EXISTS `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `genre`
CREATE TABLE IF NOT EXISTS `genre` (
  `genre_id` int NOT NULL,
  `genre_name` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `post`
CREATE TABLE IF NOT EXISTS `post` (
  `post_id` int NOT NULL,
  `post_react_counter` int DEFAULT NULL,
  `post_user_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `post_comment`
CREATE TABLE IF NOT EXISTS `post_comment` (
  `post_comment_id` int NOT NULL,
  `post_id` int DEFAULT NULL,
  `comment_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `preferences`
CREATE TABLE IF NOT EXISTS `preferences` (
  `preference_id` int NOT NULL,
  `genre_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `rate`
CREATE TABLE IF NOT EXISTS `rate` (
  `rate_id` int NOT NULL,
  `rate_user_id` int DEFAULT NULL,
  `rate_show_id` int DEFAULT NULL,
  `rate_value` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `shows`
CREATE TABLE IF NOT EXISTS `shows` (
  `show_id` int NOT NULL,
  `show_imdb_rate` int DEFAULT NULL,
  `show_current_rate` int DEFAULT NULL,
  `show_trailer` varchar(200) DEFAULT NULL,
  `show_poster` varchar(200) DEFAULT NULL,
  `show_genre_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `user_cmgroup`
CREATE TABLE IF NOT EXISTS `user_cmgroup` (
  `user_cmgroup_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `cmgroup_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `user_comment`
CREATE TABLE IF NOT EXISTS `user_comment` (
  `user_comment_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `comment_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `user_preference`
CREATE TABLE IF NOT EXISTS `user_preference` (
  `user_id` int NOT NULL,
  `genre_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `user_rate`
CREATE TABLE IF NOT EXISTS `user_rate` (
  `user_id` int NOT NULL,
  `show_id` int NOT NULL,
  `rate_value` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `user_watchlist`
CREATE TABLE IF NOT EXISTS `user_watchlist` (
  `user_id` int NOT NULL,
  `show_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `watchlist`
CREATE TABLE IF NOT EXISTS `watchlist` (
  `watchlist_id` int NOT NULL,
  `watchlist_user_id` int DEFAULT NULL,
  `watchlist_show_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------
-- Data Insertion
-- --------------------------------------------------------

-- Dumping data for table `auth_user`
INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `date_of_birth`) VALUES
(2, 'pbkdf2_sha256$870000$W1RwnQuzapmDiUWS9i78rZ$ow+9OKjNvv42+t+8oCd4/CY56p8W3Bnv5xrp6ya0aTw=', '2024-10-30 23:57:08.892723', 1, 'MASTER', '', '', '', 1, 1, '2024-10-30 22:06:04.471838', '1990-01-01');

-- Dumping data for table `authtoken_token`
INSERT INTO `authtoken_token` (`key`, `created`, `user_id`) VALUES
('5b960e3367938c801175cfcee45e6be8baadd50a', '2024-10-30 23:39:38.230385', 2);

-- Dumping data for table `auth_permission`
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add Token', 7, 'add_token'),
(26, 'Can change Token', 7, 'change_token'),
(27, 'Can delete Token', 7, 'delete_token'),
(28, 'Can view Token', 7, 'view_token'),
(29, 'Can add Token', 8, 'add_tokenproxy'),
(30, 'Can change Token', 8, 'change_tokenproxy'),
(31, 'Can delete Token', 8, 'delete_tokenproxy'),
(32, 'Can view Token', 8, 'view_tokenproxy');

-- Dumping data for table `django_admin_log`
INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES
(1, '2024-10-30 22:07:12.311172', '1', 'MASTER56', 3, '', 4, 2),
(2, '2024-10-30 23:39:38.234710', '2', '5b960e3367938c801175cfcee45e6be8baadd50a', 1, '[{\"added\": {}}]', 8, 2),
(3, '2024-10-31 00:22:59.820856', '6', 'mouaz12', 3, '', 4, 2),
(4, '2024-10-31 00:23:05.643911', '5', 'mouaz1', 3, '', 4, 2),
(5, '2024-10-31 00:23:11.504195', '4', 'mouaz', 3, '', 4, 2),
(6, '2024-10-31 00:23:18.103546', '3', 'marwan', 3, '', 4, 2);

-- Dumping data for table `django_content_type`
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'auth', 'user'),
(7, 'authtoken', 'token'),
(8, 'authtoken', 'tokenproxy'),
(5, 'contenttypes', 'contenttype'),
(6, 'sessions', 'session');

-- Dumping data for table `django_migrations`
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2024-10-30 22:02:28.922470'),
(2, 'auth', '0001_initial', '2024-10-30 22:02:29.983186'),
(3, 'admin', '0001_initial', '2024-10-30 22:02:30.250943'),
(4, 'admin', '0002_logentry_remove_auto_add', '2024-10-30 22:02:30.266284'),
(5, 'admin', '0003_logentry_add_action_flag_choices', '2024-10-30 22:02:30.283640'),
(6, 'contenttypes', '0002_remove_content_type_name', '2024-10-30 22:02:30.426376'),
(7, 'auth', '0002_alter_permission_name_max_length', '2024-10-30 22:02:30.555605'),
(8, 'auth', '0003_alter_user_email_max_length', '2024-10-30 22:02:30.600519'),
(9, 'auth', '0004_alter_user_username_opts', '2024-10-30 22:02:30.617326'),
(10, 'auth', '0005_alter_user_last_login_null', '2024-10-30 22:02:30.718824'),
(11, 'auth', '0006_require_contenttypes_0002', '2024-10-30 22:02:30.727386'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2024-10-30 22:02:30.744091'),
(13, 'auth', '0008_alter_user_username_max_length', '2024-10-30 22:02:30.861952'),
(14, 'auth', '0009_alter_user_last_name_max_length', '2024-10-30 22:02:30.978675'),
(15, 'auth', '0010_alter_group_name_max_length', '2024-10-30 22:02:31.014764'),
(16, 'auth', '0011_update_proxy_permissions', '2024-10-30 22:02:31.040244'),
(17, 'auth', '0012_alter_user_first_name_max_length', '2024-10-30 22:02:31.160269'),
(18, 'sessions', '0001_initial', '2024-10-30 22:02:31.228023'),
(19, 'authtoken', '0001_initial', '2024-10-30 23:38:27.836461'),
(20, 'authtoken', '0002_auto_20160226_1747', '2024-10-30 23:38:27.876297'),
(21, 'authtoken', '0003_tokenproxy', '2024-10-30 23:38:27.887212'),
(22, 'authtoken', '0004_alter_tokenproxy_options', '2024-10-30 23:38:27.901046');

-- Dumping data for table `django_session`
INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('uyxn2fe0z1eof6vn8ugrlsrps8qtcynd', '.eJxVjEEOwiAQRe_C2pB2Bhhw6d4zkAGmtmpoUtqV8e7apAvd_vfef6nI2zrGrckSp6LOCtTpd0ucH1J3UO5cb7POc12XKeld0Qdt-joXeV4O9-9g5DZ-614IrSWbwAcOCclRtjQ4EMMefCKUji0PIVABGmwQlzvIvcHOIDpQ7w_DwDbK:1t6IYm:aG0FUZtoVojDwyanCSxA8WQ7hGLao5SZ4vgg-qo9BF0', '2024-11-13 23:57:08.904950');

-- --------------------------------------------------------
-- Indexes
-- --------------------------------------------------------

-- Indexes for table `authtoken_token`
ALTER TABLE `authtoken_token`
  ADD PRIMARY KEY (`key`),
  ADD UNIQUE KEY `user_id` (`user_id`);

-- Indexes for table `auth_group`
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

-- Indexes for table `auth_group_permissions`
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

-- Indexes for table `auth_permission`
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

-- Indexes for table `auth_user`
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

-- Indexes for table `auth_user_groups`
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

-- Indexes for table `auth_user_user_permissions`
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

-- Indexes for table `cmgroup`
ALTER TABLE `cmgroup`
  ADD PRIMARY KEY (`cmgroup_id`),
  ADD KEY `fk_cmgroup_admin_id` (`cmgroup_admin_id`);

-- Indexes for table `comment`
ALTER TABLE `comment`
  ADD PRIMARY KEY (`comment_id`);

-- Indexes for table `django_admin_log`
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `fk_django_admin_log_user_id` (`user_id`);

-- Indexes for table `django_content_type`
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

-- Indexes for table `django_migrations`
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

-- Indexes for table `django_session`
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

-- Indexes for table `genre`
ALTER TABLE `genre`
  ADD PRIMARY KEY (`genre_id`);

-- Indexes for table `post`
ALTER TABLE `post`
  ADD PRIMARY KEY (`post_id`);

-- Indexes for table `post_comment`
ALTER TABLE `post_comment`
  ADD PRIMARY KEY (`post_comment_id`),
  ADD KEY `post_id` (`post_id`),
  ADD KEY `comment_id` (`comment_id`);

-- Indexes for table `preferences`
ALTER TABLE `preferences`
  ADD PRIMARY KEY (`preference_id`);

-- Indexes for table `rate`
ALTER TABLE `rate`
  ADD PRIMARY KEY (`rate_id`);

-- Indexes for table `shows`
ALTER TABLE `shows`
  ADD PRIMARY KEY (`show_id`);

-- Indexes for table `user_cmgroup`
ALTER TABLE `user_cmgroup`
  ADD PRIMARY KEY (`user_cmgroup_id`),
  ADD KEY `cmgroup_id` (`cmgroup_id`),
  ADD KEY `fk_user_cmgroup_user_id` (`user_id`);

-- Indexes for table `user_comment`
ALTER TABLE `user_comment`
  ADD PRIMARY KEY (`user_comment_id`),
  ADD KEY `comment_id` (`comment_id`),
  ADD KEY `fk_user_comment_user_id` (`user_id`);

-- Indexes for table `user_preference`
ALTER TABLE `user_preference`
  ADD PRIMARY KEY (`user_id`,`genre_id`),
  ADD KEY `genre_id` (`genre_id`);

-- Indexes for table `user_rate`
ALTER TABLE `user_rate`
  ADD PRIMARY KEY (`user_id`,`show_id`),
  ADD KEY `show_id` (`show_id`);

-- Indexes for table `user_watchlist`
ALTER TABLE `user_watchlist`
  ADD PRIMARY KEY (`user_id`,`show_id`),
  ADD KEY `show_id` (`show_id`);

-- Indexes for table `watchlist`
ALTER TABLE `watchlist`
  ADD PRIMARY KEY (`watchlist_id`);

-- --------------------------------------------------------
-- Auto Increment
-- --------------------------------------------------------

-- AUTO_INCREMENT for table `auth_group`
ALTER TABLE `auth_group`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `auth_group_permissions`
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `auth_permission`
ALTER TABLE `auth_permission`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

-- AUTO_INCREMENT for table `auth_user`
ALTER TABLE `auth_user`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

-- AUTO_INCREMENT for table `auth_user_groups`
ALTER TABLE `auth_user_groups`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `auth_user_user_permissions`
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `cmgroup`
ALTER TABLE `cmgroup`
  MODIFY `cmgroup_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `comment`
ALTER TABLE `comment`
  MODIFY `comment_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `django_admin_log`
ALTER TABLE `django_admin_log`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `django_content_type`
ALTER TABLE `django_content_type`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

-- AUTO_INCREMENT for table `django_migrations`
ALTER TABLE `django_migrations`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

-- AUTO_INCREMENT for table `genre`
ALTER TABLE `genre`
  MODIFY `genre_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `post`
ALTER TABLE `post`
  MODIFY `post_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `post_comment`
ALTER TABLE `post_comment`
  MODIFY `post_comment_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `preferences`
ALTER TABLE `preferences`
  MODIFY `preference_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `rate`
ALTER TABLE `rate`
  MODIFY `rate_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `shows`
ALTER TABLE `shows`
  MODIFY `show_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `user_cmgroup`
ALTER TABLE `user_cmgroup`
  MODIFY `user_cmgroup_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `user_comment`
ALTER TABLE `user_comment`
  MODIFY `user_comment_id` int NOT NULL AUTO_INCREMENT;

-- AUTO_INCREMENT for table `watchlist`
ALTER TABLE `watchlist`
  MODIFY `watchlist_id` int NOT NULL AUTO_INCREMENT;

-- --------------------------------------------------------
-- Constraints
-- --------------------------------------------------------

-- Constraints for table `authtoken_token`
ALTER TABLE `authtoken_token`
  ADD CONSTRAINT `authtoken_token_user_id_35299eff_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

-- Constraints for table `auth_group_permissions`
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

-- Constraints for table `auth_permission`
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

-- Constraints for table `auth_user_groups`
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `fk_auth_user_groups_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- Constraints for table `auth_user_user_permissions`
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `fk_auth_user_user_permissions_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- Constraints for table `cmgroup`
ALTER TABLE `cmgroup`
  ADD CONSTRAINT `fk_cmgroup_admin_id` FOREIGN KEY (`cmgroup_admin_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- Constraints for table `django_admin_log`
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `fk_django_admin_log_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- Constraints for table `post_comment`
ALTER TABLE `post_comment`
  ADD CONSTRAINT `post_comment_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `post` (`post_id`),
  ADD CONSTRAINT `post_comment_ibfk_2` FOREIGN KEY (`comment_id`) REFERENCES `comment` (`comment_id`);

-- Constraints for table `user_cmgroup`
ALTER TABLE `user_cmgroup`
  ADD CONSTRAINT `fk_user_cmgroup_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_cmgroup_ibfk_2` FOREIGN KEY (`cmgroup_id`) REFERENCES `cmgroup` (`cmgroup_id`);

-- Constraints for table `user_comment`
ALTER TABLE `user_comment`
  ADD CONSTRAINT `fk_user_comment_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_comment_ibfk_2` FOREIGN KEY (`comment_id`) REFERENCES `comment` (`comment_id`);

-- Constraints for table `user_preference`
ALTER TABLE `user_preference`
  ADD CONSTRAINT `fk_user_preference_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_preference_ibfk_2` FOREIGN KEY (`genre_id`) REFERENCES `genre` (`genre_id`);

-- Constraints for table `user_rate`
ALTER TABLE `user_rate`
  ADD CONSTRAINT `fk_user_rate_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_rate_ibfk_2` FOREIGN KEY (`show_id`) REFERENCES `shows` (`show_id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- Constraints for table `user_watchlist`
ALTER TABLE `user_watchlist`
  ADD CONSTRAINT `fk_user_watchlist_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user_watchlist_ibfk_2` FOREIGN KEY (`show_id`) REFERENCES `shows` (`show_id`) ON DELETE CASCADE ON UPDATE CASCADE;

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
