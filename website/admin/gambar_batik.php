<?php
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../config/session.php';
requireAdmin();
header('Location: kategori_batik.php');
exit;
