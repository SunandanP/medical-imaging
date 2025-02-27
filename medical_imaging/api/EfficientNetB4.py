import torch.nn as nn
import timm

class EfficientNetB4(nn.Module):
    def __init__(self, num_classes):
        super(EfficientNetB4, self).__init__()

        # Load the pre-trained EfficientNetB4 model from timm
        self.efficientnet_b4 = timm.create_model('tf_efficientnet_b4', pretrained=True)

        # Freeze the convolutional layers (optional, uncomment if you want to freeze)
        # for param in self.efficientnet_b4.parameters():
        #     param.requires_grad = False

        # Modify the final fully connected layer to match the number of classes
        num_ftrs = self.efficientnet_b4.get_classifier().in_features
        self.efficientnet_b4.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        x = self.efficientnet_b4(x)
        return x

