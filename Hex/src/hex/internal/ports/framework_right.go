package ports

type DbPort interface {
	CloseDbConnection()
	AddToHistory(answer int32, operation int32)(error)


}



















