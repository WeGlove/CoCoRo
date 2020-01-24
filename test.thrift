namespace csharp de.dfki.tecs.robot.baxter
namespace java de.dfki.tecs.robot.baxter
namespace cpp de.dfki.tecs.robot.baxter
namespace py de.dfki.tecs.robot.baxter
namespace rb de.dfki.tecs.robot.baxter


struct moveArm {
	1: i16 arm = 0
}

struct moveCategory{
	1: i16 category = 0
}

struct moveImg{
	1: i16 image = 0
}

struct reset{
}

struct show{
	1: i16 image = 0
}


struct shown{
	1: i16 image_shown = -1
} 

struct moved{
	1: bool success = true
}
