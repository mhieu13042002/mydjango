try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    # Nếu chưa cài pymysql (ví dụ dùng mysqlclient thay thế), bỏ qua.
    pass
