import abc


# TODO: Need spec+implement this. Will be needed when we have games with clearly carved out "roles" within them. For example, in assistance games we will need a "human" vs "assistant" role and in GAN-like games we will need a "generator" vs "discriminator" role. Many other possibilities where this becomes interesting to have. Num roles can be >= 1 in any game.
class RoleManager(abc.ABC):
    @abc.abstractmethod
    def TBD(self):
        pass
