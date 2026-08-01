class EmbeddingModel(BaseModel):
  model_name: str
  model: Optional[Any] = None
  image_processor: Optional[Any] = None
  hidden_dim: Optional[int] = None

  class Config:
    extra = 'forbid'
    use_enum_values = True
    protected_namespaces = () # 可以写 model开头的字段，注意不要使用model_id，会冲突
